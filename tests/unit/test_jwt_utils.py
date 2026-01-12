"""Unit tests for JWTUtils."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest

from infrastructure.auth import JWTUtils


@pytest.fixture
def test_user_id():
    """Sample user UUID for testing."""
    return uuid4()


@pytest.fixture
def test_telegram_id():
    """Sample Telegram ID for testing."""
    return "123456789"


@pytest.fixture
def mock_settings():
    """Mock settings for JWT secret (env vars set in conftest.py)."""
    from config.settings import get_settings

    # Get settings instance (env vars already set in conftest.py)
    settings = get_settings()
    return settings


class TestJWTUtils:
    """Test suite for JWTUtils."""

    def test_create_token(self, test_user_id, test_telegram_id, mock_settings):
        """Test creating a JWT token."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id, expires_in_hours=24)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_custom_expiration(self, test_user_id, test_telegram_id, mock_settings):
        """Test creating a token with custom expiration."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id, expires_in_hours=1)

        # Decode to verify expiration
        payload = jwt.decode(token, mock_settings.jwt_secret_key, algorithms=["HS256"])

        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=UTC)

        # Should be ~1 hour difference
        delta = exp_time - iat_time
        assert 3500 <= delta.total_seconds() <= 3700  # Allow ~100s margin

    def test_decode_token_valid(self, test_user_id, test_telegram_id, mock_settings):
        """Test decoding a valid JWT token."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)
        payload = JWTUtils.decode_token(token)

        assert payload is not None
        assert payload["user_id"] == str(test_user_id)
        assert payload["telegram_id"] == test_telegram_id
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_token_invalid(self, mock_settings):
        """Test decoding an invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = JWTUtils.decode_token(invalid_token)

        assert payload is None

    def test_decode_token_expired(self, test_user_id, test_telegram_id, mock_settings):
        """Test decoding an expired token."""
        # Create token with past expiration
        payload_data = {
            "user_id": str(test_user_id),
            "telegram_id": test_telegram_id,
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "exp": datetime.now(UTC) - timedelta(hours=1)  # Expired
        }

        expired_token = jwt.encode(
            payload_data,
            mock_settings.jwt_secret_key,
            algorithm="HS256"
        )

        payload = JWTUtils.decode_token(expired_token)

        assert payload is None

    def test_decode_token_wrong_secret(self, test_user_id, test_telegram_id, mock_settings):
        """Test decoding a token signed with wrong secret."""
        # Create token with different secret
        wrong_token = jwt.encode(
            {
                "user_id": str(test_user_id),
                "telegram_id": test_telegram_id,
                "exp": datetime.now(UTC) + timedelta(hours=1)
            },
            "wrong-secret-key",
            algorithm="HS256"
        )

        payload = JWTUtils.decode_token(wrong_token)

        assert payload is None

    def test_extract_user_id_from_token(self, test_user_id, test_telegram_id, mock_settings):
        """Test extracting user_id from a valid token."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)
        extracted_id = JWTUtils.extract_user_id_from_token(token)

        assert isinstance(extracted_id, UUID)
        assert extracted_id == test_user_id

    def test_extract_user_id_from_invalid_token(self, mock_settings):
        """Test extracting user_id from an invalid token."""
        extracted_id = JWTUtils.extract_user_id_from_token("invalid.token")

        assert extracted_id is None

    def test_extract_user_id_missing_field(self, test_telegram_id, mock_settings):
        """Test extracting user_id from token missing user_id field."""
        # Create token without user_id
        token = jwt.encode(
            {
                "telegram_id": test_telegram_id,
                "exp": datetime.now(UTC) + timedelta(hours=1)
            },
            mock_settings.jwt_secret_key,
            algorithm="HS256"
        )

        extracted_id = JWTUtils.extract_user_id_from_token(token)

        assert extracted_id is None

    def test_extract_from_request_header_bearer(self, test_user_id, test_telegram_id, mock_settings):
        """Test extracting user_id from Authorization header with Bearer prefix."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)
        auth_header = f"Bearer {token}"

        extracted_id = JWTUtils.extract_from_request_header(auth_header)

        assert isinstance(extracted_id, UUID)
        assert extracted_id == test_user_id

    def test_extract_from_request_header_jwt_prefix(self, test_user_id, test_telegram_id, mock_settings):
        """Test extracting user_id from Authorization header with JWT prefix."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)
        auth_header = f"JWT {token}"

        extracted_id = JWTUtils.extract_from_request_header(auth_header)

        assert isinstance(extracted_id, UUID)
        assert extracted_id == test_user_id

    def test_extract_from_request_header_no_prefix(self, test_user_id, test_telegram_id, mock_settings):
        """Test extracting user_id from raw token (no prefix)."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)

        extracted_id = JWTUtils.extract_from_request_header(token)

        assert isinstance(extracted_id, UUID)
        assert extracted_id == test_user_id

    def test_extract_from_request_header_invalid_scheme(self, test_user_id, test_telegram_id, mock_settings):
        """Test invalid authorization scheme."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)
        auth_header = f"Basic {token}"  # Wrong scheme

        extracted_id = JWTUtils.extract_from_request_header(auth_header)

        assert extracted_id is None

    def test_extract_from_request_header_none(self, mock_settings):
        """Test extracting from None header."""
        extracted_id = JWTUtils.extract_from_request_header(None)

        assert extracted_id is None

    def test_token_payload_structure(self, test_user_id, test_telegram_id, mock_settings):
        """Test the complete structure of token payload."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id, expires_in_hours=12)
        payload = JWTUtils.decode_token(token)

        # Verify all expected fields
        assert "user_id" in payload
        assert "telegram_id" in payload
        assert "iat" in payload
        assert "exp" in payload

        # Verify data types
        assert isinstance(payload["user_id"], str)
        assert isinstance(payload["telegram_id"], str)
        assert isinstance(payload["iat"], int)  # Unix timestamp
        assert isinstance(payload["exp"], int)

        # Verify UUID format
        try:
            UUID(payload["user_id"])
        except ValueError:
            pytest.fail("user_id is not a valid UUID")

    def test_case_insensitive_scheme(self, test_user_id, test_telegram_id, mock_settings):
        """Test that authorization scheme is case-insensitive."""
        token = JWTUtils.create_token(test_user_id, test_telegram_id)

        # Test various capitalizations
        for prefix in ["bearer", "BEARER", "Bearer", "bEaReR"]:
            auth_header = f"{prefix} {token}"
            extracted_id = JWTUtils.extract_from_request_header(auth_header)
            assert extracted_id == test_user_id
