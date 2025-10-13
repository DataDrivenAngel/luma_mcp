import os
import pytest
from src.config import Settings, validate_api_key, get_luma_api_url


class TestConfig:
    """Test configuration management."""

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.luma_base_url == "https://api.lu.ma"
        assert settings.luma_api_version == "public/v1"
        assert settings.host == "localhost"
        assert settings.port == 8000
        assert settings.debug is False

    def test_settings_from_env(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("LUMA_API_KEY", "test_key")
        monkeypatch.setenv("LUMA_HOST", "0.0.0.0")
        monkeypatch.setenv("LUMA_PORT", "9000")
        monkeypatch.setenv("LUMA_DEBUG", "true")

        settings = Settings()
        assert settings.luma_api_key == "test_key"
        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.debug is True

    def test_get_luma_api_url(self):
        """Test API URL construction."""
        url = get_luma_api_url("event/create")
        assert url == "https://api.lu.ma/public/v1/event/create"

    def test_validate_api_key_valid(self, monkeypatch):
        """Test API key validation with valid key."""
        monkeypatch.setenv("LUMA_API_KEY", "valid_key")
        assert validate_api_key() is True

    def test_validate_api_key_invalid(self, monkeypatch):
        """Test API key validation with invalid/empty key."""
        monkeypatch.setenv("LUMA_API_KEY", "")
        assert validate_api_key() is False

        monkeypatch.delenv("LUMA_API_KEY", raising=False)
        assert validate_api_key() is False

    def test_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        settings = Settings()
        assert settings.rate_limit_get_requests == 500
        assert settings.rate_limit_post_requests == 100
        assert settings.rate_limit_window_seconds == 300
        assert settings.rate_limit_block_duration_seconds == 60