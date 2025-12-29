"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables with defaults.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables:
        DATABASE_URL: Database connection string (default: sqlite:///./inventory.db)
        LOG_LEVEL: Logging level (default: INFO)
        CORS_ORIGINS: Comma-separated allowed origins (default: *)
        API_PREFIX: API route prefix (default: /v1)
        APP_NAME: Application name (default: Inventory Management API)
        DEBUG: Debug mode (default: False)
    """

    # Database configuration
    DATABASE_URL: str = "sqlite:///./inventory.db"
    DATABASE_ECHO: bool = False

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS configuration
    CORS_ORIGINS: str = "*"  # Comma-separated list
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # API configuration
    API_PREFIX: str = "/v1"
    APP_NAME: str = "Inventory Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Feature flags
    ENABLE_EVENT_PERSISTENCE: bool = True
    ENABLE_METRICS: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
