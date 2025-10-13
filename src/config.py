import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LUMA API Configuration
    luma_api_key: str = ""
    luma_base_url: str = "https://api.lu.ma"
    luma_api_version: str = "public/v1"

    # Server Configuration
    host: str = "localhost"
    port: int = 8000
    debug: bool = False

    # Rate Limiting
    rate_limit_get_requests: int = 500
    rate_limit_post_requests: int = 100
    rate_limit_window_seconds: int = 300  # 5 minutes
    rate_limit_block_duration_seconds: int = 60  # 1 minute

    # Request Configuration
    request_timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

    class Config:
        env_file = ".env"
        env_prefix = "LUMA_"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_luma_api_url(endpoint: str) -> str:
    """Construct full LUMA API URL for an endpoint."""
    return f"{settings.luma_base_url}/{settings.luma_api_version}/{endpoint}"


def validate_api_key() -> bool:
    """Validate that LUMA API key is configured."""
    return bool(settings.luma_api_key and settings.luma_api_key.strip())