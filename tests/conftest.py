"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(monkeypatch_session):
    """Setup test environment variables."""
    # Mock settings for tests
    monkeypatch_session.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch_session.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch_session.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
    monkeypatch_session.setenv("ENCRYPTION_KEY", "test-encryption-key-32-bytes!!")
    monkeypatch_session.setenv("APP_ENV", "test")
    monkeypatch_session.setenv("DEBUG", "true")
    monkeypatch_session.setenv("CORS_ENABLED", "false")
    monkeypatch_session.setenv("TELEGRAM_BOT_TOKEN", "test-bot-token")
    monkeypatch_session.setenv("GROQ_API_KEY", "test-groq-key")


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch for environment setup."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()
