"""Tests for uiautodev manager."""
import pytest
from unittest.mock import patch, MagicMock
from core.uiautodev_manager import UiautodevManager


class TestUiautodevManager:
    """Test UiautodevManager."""

    def setup_method(self):
        self.manager = UiautodevManager(host="127.0.0.1", port=20243)

    def test_init(self):
        """Test manager initialization."""
        assert self.manager.host == "127.0.0.1"
        assert self.manager.port == 20243
        assert self.manager.server_url == "http://127.0.0.1:20243"
        assert self.manager.process is None

    def test_get_status_not_running(self):
        """Test get_status when server is not running."""
        with patch("core.uiautodev_manager.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            status = self.manager.get_status()
            assert status["running"] is False
            assert status["url"] == "https://uiauto2.devsleep.com"
            assert status["host"] == "127.0.0.1"
            assert status["port"] == 20243

    def test_get_device_url(self):
        """Test getting device debug URL."""
        url = self.manager.get_device_url("abc123")
        assert url == "https://uiauto2.devsleep.com/android/abc123"

    def test_get_device_url_with_platform(self):
        """Test getting device debug URL with custom platform."""
        url = self.manager.get_device_url("abc123", platform="iOS")
        assert url == "https://uiauto2.devsleep.com/iOS/abc123"
