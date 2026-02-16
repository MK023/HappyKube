"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    app_name: str = Field(default="HappyKube", description="Application name")
    app_version: str = Field(default="3.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=5000, ge=1, le=65535, description="API port")
    api_workers: int = Field(default=2, ge=1, le=32, description="Number of worker processes")
    api_timeout: int = Field(default=120, ge=30, le=300, description="Request timeout in seconds")

    # Database (supports both DATABASE_URL and individual fields)
    database_url: str | None = Field(default=None, description="Full database URL")
    db_host: str | None = Field(default=None, description="PostgreSQL host")
    db_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    db_name: str | None = Field(default=None, description="Database name")
    db_user: str | None = Field(default=None, description="Database user")
    db_password: str | None = Field(default=None, description="Database password")
    db_pool_size: int = Field(default=3, ge=1, le=100, description="Connection pool size")
    db_max_overflow: int = Field(default=2, ge=0, le=100, description="Max overflow connections")
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    # Redis (supports both REDIS_URL and individual fields)
    redis_url: str | None = Field(default=None, description="Full Redis URL")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_password: str | None = Field(default=None, description="Redis password")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis")
    redis_cache_ttl: int = Field(
        default=3600, ge=60, le=86400, description="Default cache TTL in seconds"
    )

    # Security
    encryption_key: str | None = Field(default=None, description="Fernet encryption key for PII")
    jwt_secret_key: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(
        default=1440, ge=5, le=43200, description="JWT expiration in minutes"
    )
    api_keys: list[str] | None = Field(
        default=None, description="Allowed API keys (comma-separated)"
    )
    internal_api_key: str = Field(
        default="",
        description="Internal API key for bot-to-API communication (use existing API key)",
    )

    # Telegram Bot
    telegram_bot_token: str = Field(default="", description="Telegram bot token")
    telegram_webhook_secret: str = Field(
        default="", description="Secret token for webhook validation (HappyKube 3.0)"
    )
    telegram_api_timeout: int = Field(default=30, ge=10, le=60, description="Telegram API timeout")

    # ML API - Groq (Llama 3.3 70B)
    groq_api_key: str = Field(default="", description="Groq API key for Llama inference (free)")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_default: str = Field(default="100 per minute", description="Default rate limit")
    rate_limit_storage_url: str | None = Field(
        default=None, description="Rate limit storage URL (Redis)"
    )

    # CORS
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] | None = Field(
        default=None,
        description="Allowed CORS origins",
    )

    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(
        default=9090, ge=1, le=65535, description="Prometheus metrics port"
    )

    # Sentry (optional)
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN for error tracking")
    sentry_traces_sample_rate: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Sentry traces sample rate"
    )

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | list[str] | None) -> list[str] | None:
        """Parse comma-separated API keys."""
        if v is None:
            return None
        if isinstance(v, str):
            keys = [key.strip() for key in v.split(",") if key.strip()]
            return keys if keys else None
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str] | None) -> list[str] | None:
        """Parse comma-separated CORS origins."""
        if v is None:
            return ["http://localhost:3000"]
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:3000"]
        return v

    def get_database_url(self) -> str:
        """Get PostgreSQL connection URL."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_url:
            return self.redis_url
        scheme = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate settings after initialization."""
        # Validate database connection can be built
        if not self.database_url and not all(
            [self.db_host, self.db_name, self.db_user, self.db_password]
        ):
            raise ValueError(
                "Either DATABASE_URL or all of (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) must be set"
            )

        # Validate Redis connection can be built
        if not self.redis_url and not self.redis_host:
            raise ValueError("Either REDIS_URL or REDIS_HOST must be set")

        # Validate production settings
        if self.is_production:
            if self.debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if not self.encryption_key:
                raise ValueError("Encryption key must be set in production")
            if not self.sentry_dsn:
                # Log as info instead of warning - Sentry is optional
                import logging

                logging.getLogger(__name__).info(
                    "Sentry DSN not configured - error tracking disabled"
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore
