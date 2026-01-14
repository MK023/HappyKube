"""Axiom integration for centralized logging."""

import atexit
import threading
from datetime import datetime
from queue import Queue
from typing import Any

from structlog.types import EventDict, WrappedLogger

from .logging import get_logger
from .settings import get_settings

logger = get_logger(__name__)

# Global Axiom client instance
_axiom_client: Any = None
_axiom_enabled = False


def init_axiom() -> None:
    """
    Initialize Axiom client for centralized logging.

    Only initializes if:
    - AXIOM_API_TOKEN is configured
    - Running in production or staging environment

    This function is safe to call multiple times (idempotent).
    """
    global _axiom_client, _axiom_enabled

    settings = get_settings()

    if not settings.axiom_api_token:
        logger.info("Axiom not configured (AXIOM_API_TOKEN missing)")
        return

    if settings.is_development:
        logger.info("Axiom disabled in development environment", env=settings.app_env)
        return

    try:
        from axiom_py import Client

        # Client uses positional arguments: Client(token, org_id)
        _axiom_client = Client(
            settings.axiom_api_token,
            settings.axiom_org_id,
        )

        _axiom_enabled = True

        logger.info(
            "Axiom initialized",
            dataset=settings.axiom_dataset,
            url=settings.axiom_url,
            environment=settings.app_env,
        )

    except ImportError as e:
        logger.warning("Axiom library not installed, logging disabled", error=str(e))
    except Exception as e:
        logger.error("Failed to initialize Axiom (non-fatal)", error=str(e))


class AxiomProcessor:
    """
    Structlog processor that sends logs to Axiom in batches.

    Features:
    - Batches logs for efficiency (reduces API calls)
    - Background thread for async sending
    - Graceful error handling (never crashes the app)
    - Auto-flush on shutdown
    """

    def __init__(self, batch_size: int = 50, flush_interval: float = 5.0):
        """
        Initialize the Axiom processor.

        Args:
            batch_size: Number of logs to batch before sending
            flush_interval: Seconds between automatic flushes
        """
        self.settings = get_settings()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: Queue[dict[str, Any]] = Queue(maxsize=1000)
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

        # Start background flush thread
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()

        # Register cleanup on exit
        atexit.register(self._cleanup)

        logger.debug("AxiomProcessor initialized", batch_size=batch_size)

    def __call__(self, logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
        """
        Process a log event and queue it for sending to Axiom.

        Args:
            logger: The wrapped logger instance
            method_name: Logging method name (info, error, etc.)
            event_dict: The log event data

        Returns:
            The unmodified event_dict (pass-through)
        """
        if not _axiom_enabled or not _axiom_client:
            return event_dict

        try:
            # Transform structlog event to Axiom format
            axiom_event = {
                "_time": datetime.utcnow().isoformat() + "Z",
                "level": method_name,
                "message": event_dict.get("event", ""),
                **{k: v for k, v in event_dict.items() if k != "event"},
            }

            # Add to buffer (non-blocking)
            try:
                self.buffer.put_nowait(axiom_event)
            except Exception as e:
                # Buffer full - drop log to avoid blocking app
                logger.debug("Axiom buffer full, dropping log", error=str(e))

        except Exception as e:
            # Never let logging errors crash the app
            logger.debug("Failed to queue log for Axiom", error=str(e))

        return event_dict

    def _flush_worker(self) -> None:
        """Background worker that flushes logs to Axiom periodically."""
        import time

        batch: list[dict[str, Any]] = []

        while not self._stop_event.is_set():
            try:
                # Collect batch or wait for timeout
                while len(batch) < self.batch_size and not self._stop_event.is_set():
                    try:
                        event = self.buffer.get(timeout=self.flush_interval)
                        batch.append(event)
                    except Exception:
                        # Timeout - flush what we have
                        break

                if batch:
                    self._send_batch(batch)
                    batch = []

                time.sleep(0.1)  # Small delay to prevent busy loop

            except Exception as e:
                logger.debug("Error in Axiom flush worker", error=str(e))
                time.sleep(1)  # Back off on error

    def _send_batch(self, events: list[dict[str, Any]]) -> None:
        """
        Send a batch of events to Axiom.

        Args:
            events: List of log events to send
        """
        if not _axiom_client or not events:
            return

        try:
            _axiom_client.ingest(
                dataset=self.settings.axiom_dataset,
                events=events,
            )

            logger.debug("Sent batch to Axiom", count=len(events))

        except Exception as e:
            # Log error but don't crash (graceful degradation)
            logger.debug("Failed to send logs to Axiom", error=str(e), count=len(events))

    def _cleanup(self) -> None:
        """Cleanup on shutdown - flush remaining logs."""
        logger.debug("Flushing remaining logs to Axiom")

        # Signal worker to stop
        self._stop_event.set()

        # Flush remaining logs
        remaining = []
        while not self.buffer.empty():
            try:
                remaining.append(self.buffer.get_nowait())
            except Exception:
                break

        if remaining:
            self._send_batch(remaining)

        logger.debug("Axiom cleanup completed", flushed=len(remaining))


# Global processor instance
_processor: AxiomProcessor | None = None


def get_axiom_processor() -> AxiomProcessor:
    """
    Get or create the global Axiom processor instance.

    Returns:
        AxiomProcessor instance
    """
    global _processor

    if _processor is None:
        _processor = AxiomProcessor()

    return _processor
