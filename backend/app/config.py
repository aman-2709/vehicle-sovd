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

    # gRPC vehicle communication configuration
    VEHICLE_ENDPOINT_URL: str = "localhost:50051"
    VEHICLE_USE_TLS: bool = False
    VEHICLE_GRPC_TIMEOUT: int = 30  # seconds
    VEHICLE_MAX_RETRIES: int = 3
    VEHICLE_RETRY_BASE_DELAY: float = 1.0  # seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )


# Singleton settings instance
# Loaded once at module import and reused throughout the application
settings = Settings()  # type: ignore[call-arg]
