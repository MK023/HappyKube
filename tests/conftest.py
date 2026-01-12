"""Pytest configuration and shared fixtures."""

import os
import pytest
import sys
from pathlib import Path

# Set environment variables BEFORE any imports (must be at module level)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-bytes!!")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("CORS_ENABLED", "false")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-bot-token")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
