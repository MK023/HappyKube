"""Database connection management with SQLAlchemy 2.0."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import get_logger, settings

logger = get_logger(__name__)


# Global engine instance (created once)
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """
    Get or create SQLAlchemy engine with connection pooling.

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        logger.info(
            "Creating database engine",
            host=settings.db_host,
            database=settings.db_name,
            pool_size=settings.db_pool_size,
        )

        # Create engine with connection pooling
        _engine = create_engine(
            settings.get_database_url(),
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=settings.db_echo,  # Log SQL queries if enabled
        )

        # Add connection event listeners for debugging
        @event.listens_for(_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):  # type: ignore
            """Log when new connection is established."""
            logger.debug("Database connection established")

        @event.listens_for(_engine, "close")
        def receive_close(dbapi_conn, connection_record):  # type: ignore
            """Log when connection is closed."""
            logger.debug("Database connection closed")

        logger.info("Database engine created successfully")

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """
    Get or create session factory.

    Returns:
        SQLAlchemy sessionmaker
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Don't expire objects after commit
        )
        logger.info("Session factory created")

    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Automatically commits on success, rolls back on error.

    Usage:
        with get_db_session() as session:
            user = session.query(UserModel).first()
            session.add(new_record)
            # Commit happens automatically

    Yields:
        SQLAlchemy Session

    Raises:
        Exception: Any database error (session is rolled back)
    """
    factory = get_session_factory()
    session = factory()

    try:
        logger.debug("Database session started")
        yield session
        session.commit()
        logger.debug("Database session committed")
    except Exception as e:
        logger.error("Database session error, rolling back", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


def init_database() -> None:
    """
    Initialize database tables (create if not exists).

    Note: In production, use Alembic migrations instead.
    This is mainly for testing and development.
    """
    from .models import Base

    engine = get_engine()
    logger.info("Creating database tables if they don't exist")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


def close_database() -> None:
    """
    Close database connections and dispose engine.

    Call this on application shutdown.
    """
    global _engine, _session_factory

    if _engine is not None:
        logger.info("Closing database engine")
        _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")


def health_check() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if database is reachable, False otherwise
    """
    try:
        with get_db_session() as session:
            # Simple query to test connection
            session.execute("SELECT 1")  # type: ignore
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False
