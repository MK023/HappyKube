"""Field-level encryption for sensitive data (PII compliance)."""

from cryptography.fernet import Fernet

from config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class FieldEncryption:
    """
    Handles AES-256 encryption/decryption for database fields.

    Uses Fernet (symmetric encryption) with key from settings.
    All PII data (user text, etc.) is encrypted at rest.
    """

    def __init__(self, encryption_key: str | None = None) -> None:
        """
        Initialize encryption handler.

        Args:
            encryption_key: Base64-encoded Fernet key (optional, defaults to settings)

        Raises:
            ValueError: If encryption key is invalid
        """
        key = encryption_key or settings.encryption_key

        try:
            self._fernet = Fernet(key.encode())
            logger.info("Field encryption initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize encryption", error=str(e))
            raise ValueError(f"Invalid encryption key: {e}") from e

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt plaintext string to bytes.

        Args:
            plaintext: Text to encrypt

        Returns:
            Encrypted bytes

        Raises:
            ValueError: If encryption fails
        """
        if not plaintext:
            return b""

        try:
            encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
            logger.debug("Text encrypted successfully", length=len(plaintext))
            return encrypted
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise ValueError(f"Encryption failed: {e}") from e

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt bytes to plaintext string.

        Args:
            ciphertext: Encrypted bytes

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If decryption fails
        """
        if not ciphertext:
            return ""

        try:
            decrypted = self._fernet.decrypt(ciphertext)
            plaintext = decrypted.decode("utf-8")
            logger.debug("Text decrypted successfully")
            return plaintext
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise ValueError(f"Decryption failed: {e}") from e

    def encrypt_if_needed(self, value: str | bytes) -> bytes:
        """
        Encrypt value if it's a string, return as-is if already bytes.

        Args:
            value: String or bytes

        Returns:
            Encrypted bytes
        """
        if isinstance(value, bytes):
            return value
        return self.encrypt(value)

    def decrypt_if_needed(self, value: bytes | str) -> str:
        """
        Decrypt value if it's bytes, return as-is if already string.

        Args:
            value: Bytes or string

        Returns:
            Decrypted string
        """
        if isinstance(value, str):
            return value
        return self.decrypt(value)


# Singleton instance for application-wide use
_encryption_instance: FieldEncryption | None = None


def get_encryption() -> FieldEncryption:
    """
    Get singleton encryption instance.

    Returns:
        FieldEncryption instance
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = FieldEncryption()
    return _encryption_instance
