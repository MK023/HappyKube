"""Unit tests for APIKeyRepository."""

from datetime import datetime, timedelta
from uuid import UUID

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from infrastructure.database.models import APIKeyModel
from infrastructure.repositories import APIKeyRepository


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Create only the tables needed for API key tests (avoid JSONB issues)
    # EmotionModel uses JSONB which is PostgreSQL-only
    APIKeyModel.__table__.create(engine)

    yield engine

    # Cleanup
    APIKeyModel.__table__.drop(engine)


@pytest.fixture
def api_key_repo(in_memory_db):
    """Create APIKeyRepository instance."""
    return APIKeyRepository(in_memory_db)


@pytest.fixture
def sample_api_key():
    """Sample API key for testing."""
    return "HK_P_test123abc456def789ghi012jkl345mno"


class TestAPIKeyRepository:
    """Test suite for APIKeyRepository."""

    def test_create_key(self, api_key_repo, sample_api_key):
        """Test creating a new API key."""
        # Create key
        model = api_key_repo.create_key(
            api_key=sample_api_key, name="Test Key", rate_limit_per_minute=100
        )

        # Assertions
        assert isinstance(model.id, UUID)
        assert model.name == "Test Key"
        assert model.is_active is True
        assert model.rate_limit_per_minute == 100
        assert model.expires_at is None
        assert model.last_used_at is None

        # Verify bcrypt hash
        assert bcrypt.checkpw(sample_api_key.encode(), model.key_hash.encode())

    def test_create_key_with_expiration(self, api_key_repo, sample_api_key):
        """Test creating an API key with expiration."""
        expires = datetime.now() + timedelta(days=30)

        model = api_key_repo.create_key(
            api_key=sample_api_key,
            name="Expiring Key",
            rate_limit_per_minute=50,
            expires_at=expires,
        )

        assert model.expires_at is not None
        assert model.expires_at == expires

    def test_validate_key_success(self, api_key_repo, sample_api_key):
        """Test validating a valid API key."""
        # Create key
        created = api_key_repo.create_key(
            api_key=sample_api_key, name="Valid Key", rate_limit_per_minute=150
        )

        # Validate key
        is_valid, key_id, rate_limit = api_key_repo.validate_key(sample_api_key)

        assert is_valid is True
        assert key_id == created.id
        assert rate_limit == 150

    def test_validate_key_invalid(self, api_key_repo, sample_api_key):
        """Test validating an invalid API key."""
        # Create key
        api_key_repo.create_key(api_key=sample_api_key, name="Valid Key", rate_limit_per_minute=100)

        # Try to validate wrong key
        is_valid, key_id, rate_limit = api_key_repo.validate_key("HK_P_wrong_key_123")

        assert is_valid is False
        assert key_id is None
        assert rate_limit is None

    def test_validate_key_expired(self, api_key_repo, sample_api_key, in_memory_db):
        """Test validating an expired API key."""
        # Create key with past expiration
        expires = datetime.now() - timedelta(days=1)

        api_key_repo.create_key(api_key=sample_api_key, name="Expired Key", expires_at=expires)

        # Validate key
        is_valid, key_id, rate_limit = api_key_repo.validate_key(sample_api_key)

        assert is_valid is False
        assert key_id is None

    def test_validate_key_inactive(self, api_key_repo, sample_api_key, in_memory_db):
        """Test validating an inactive API key."""
        # Create and then deactivate key
        created = api_key_repo.create_key(api_key=sample_api_key, name="Inactive Key")

        api_key_repo.deactivate_key(created.id)

        # Validate key
        is_valid, key_id, rate_limit = api_key_repo.validate_key(sample_api_key)

        assert is_valid is False

    def test_validate_key_updates_last_used(self, api_key_repo, sample_api_key, in_memory_db):
        """Test that validating a key updates last_used_at."""
        # Create key
        created = api_key_repo.create_key(api_key=sample_api_key, name="Usage Tracking Key")

        # Verify last_used_at is None initially
        assert created.last_used_at is None

        # Validate key
        api_key_repo.validate_key(sample_api_key)

        # Check that last_used_at was updated
        with Session(in_memory_db) as session:
            updated = session.get(APIKeyModel, created.id)
            assert updated.last_used_at is not None

    def test_deactivate_key(self, api_key_repo, sample_api_key):
        """Test deactivating an API key."""
        # Create key
        created = api_key_repo.create_key(api_key=sample_api_key, name="Key to Deactivate")

        # Deactivate
        success = api_key_repo.deactivate_key(created.id)

        assert success is True

        # Verify it's deactivated
        is_valid, _, _ = api_key_repo.validate_key(sample_api_key)
        assert is_valid is False

    def test_deactivate_key_not_found(self, api_key_repo):
        """Test deactivating a non-existent API key."""
        from uuid import uuid4

        fake_id = uuid4()
        success = api_key_repo.deactivate_key(fake_id)

        assert success is False

    def test_list_keys_active_only(self, api_key_repo, in_memory_db):
        """Test listing only active keys."""
        # Create active keys
        api_key_repo.create_key("HK_P_key1", "Active Key 1")
        api_key_repo.create_key("HK_P_key2", "Active Key 2")

        # Create inactive key
        inactive = api_key_repo.create_key("HK_P_key3", "Inactive Key")
        api_key_repo.deactivate_key(inactive.id)

        # List active only
        keys = api_key_repo.list_keys(include_inactive=False)

        assert len(keys) == 2
        assert all(k.is_active for k in keys)

    def test_list_keys_include_inactive(self, api_key_repo, in_memory_db):
        """Test listing all keys including inactive."""
        # Create keys
        api_key_repo.create_key("HK_P_key1", "Active Key")
        inactive = api_key_repo.create_key("HK_P_key2", "Inactive Key")
        api_key_repo.deactivate_key(inactive.id)

        # List all keys
        keys = api_key_repo.list_keys(include_inactive=True)

        assert len(keys) == 2
        assert sum(1 for k in keys if k.is_active) == 1
        assert sum(1 for k in keys if not k.is_active) == 1

    def test_multiple_keys_different_hashes(self, api_key_repo):
        """Test that bcrypt generates different hashes for different keys."""
        key1 = api_key_repo.create_key("HK_P_key_one", "Key 1")
        key2 = api_key_repo.create_key("HK_P_key_two", "Key 2")

        # Different keys should have different hashes
        assert key1.key_hash != key2.key_hash

    def test_bcrypt_salt_uniqueness(self, api_key_repo):
        """Test that bcrypt generates different hashes for same key (different salt)."""
        same_key = "HK_P_identical_key_123"

        model1 = api_key_repo.create_key(same_key, "First")
        model2 = api_key_repo.create_key(same_key, "Second")

        # Same key, different salt = different hash
        assert model1.key_hash != model2.key_hash

        # But both should validate
        is_valid1, _, _ = api_key_repo.validate_key(same_key)
        assert is_valid1 is True
