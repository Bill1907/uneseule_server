"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Uneseule Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # CORS
    CORS_ORIGINS: str | list[str] = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str | list[str] = "*"
    CORS_ALLOW_HEADERS: str | list[str] = "*"

    # Database (PostgreSQL)
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_SESSION: int = 1800  # 30 minutes
    REDIS_TTL_CACHE: int = 300  # 5 minutes

    # MongoDB
    MONGODB_URL: str
    MONGODB_DATABASE: str = "uneseule"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_BCRYPT_ROUNDS: int = 12

    # ElevenLabs Integration
    ELEVENLABS_API_KEY: str
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    ELEVENLABS_VOICE_ID: str  # Default voice for toys
    ELEVENLABS_AGENT_ID: str  # Conversational AI Agent ID

    # Payment Gateway
    PAYMENT_PROVIDER: Literal["stripe", "toss"] = "stripe"
    STRIPE_API_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    TOSS_CLIENT_KEY: str | None = None
    TOSS_SECRET_KEY: str | None = None

    # Rate Limiting
    RATE_LIMIT_FREE: str = "50/day"
    RATE_LIMIT_BASIC: str = "200/day"
    RATE_LIMIT_PREMIUM: str = "unlimited"
    RATE_LIMIT_GLOBAL: str = "1000/minute"

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str | PostgresDsn) -> str:
        """Validate and convert database URL to string."""
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("CORS_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def parse_cors_settings(cls, v: str | list[str]) -> list[str]:
        """Parse CORS settings from comma-separated string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [item.strip() for item in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
