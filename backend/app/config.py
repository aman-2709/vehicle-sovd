"""
Application configuration module.

Uses pydantic-settings to load configuration from environment variables or .env file.
All sensitive values (database credentials, secrets) must be provided via environment.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Reads from environment variables or .env file in the project root.
    """

    # Database configuration
    DATABASE_URL: str

    # Redis configuration
    REDIS_URL: str

    # JWT authentication configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15

    # Logging configuration
    LOG_LEVEL: str = "INFO"

    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )


# Singleton settings instance
# Loaded once at module import and reused throughout the application
settings = Settings()  # type: ignore[call-arg]
