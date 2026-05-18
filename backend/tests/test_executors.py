"""Tests for executor layer."""
import pytest
from unittest.mock import MagicMock, patch
from executors.base_executor import BaseExecutor
from executors.android_executor import AndroidExecutor
from executors.script_executor import ScriptExecutor


class TestBaseExecutor:
    """Test BaseExecutor abstract class."""

    def test_base_executor_is_abstract(self):
        """Test that BaseExecutor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseExecutor()


class TestAndroidExecutor:
    """Test AndroidExecutor."""

    def setup_method(self):
        self.executor = AndroidExecutor()

    def test_executor_init(self):
        """Test AndroidExecutor initialization."""
        assert self.executor.d is None
        assert self.executor.logs == []
        assert self.executor.screenshots == []
        assert self.executor.current_step == 0

    def test_log(self):
        """Test logging functionality."""
        entry = self.executor._log("test message")
        assert entry["message"] == "test message"
        assert entry["level"] == "INFO"
        assert len(self.executor.logs) == 1

    def test_log_error(self):
        """Test error logging."""
        entry = self.executor._log("error message", "ERROR")
        assert entry["level"] == "ERROR"
        assert len(self.executor.logs) == 1

    def test_log_includes_timestamp(self):
        """Test that log entries include timestamp."""
        entry = self.executor._log("message")
        assert "timestamp" in entry
        assert entry["timestamp"] is not None


class TestScriptExecutor:
    """Test ScriptExecutor."""

    def setup_method(self):
        self.executor = ScriptExecutor()

    def test_executor_init(self):
        """Test ScriptExecutor initialization."""
        assert self.executor.process is None
        assert self.executor.logs == []

    def test_log(self):
        """Test logging functionality."""
        entry = self.executor._log("test message")
        assert entry["message"] == "test message"
        assert entry["level"] == "INFO"
        assert len(self.executor.logs) == 1

    def test_get_device_info(self):
        """Test getting device info."""
        from models.device import Device
        device = Device(id="abc123", serial="abc123", name="Test", platform="android")
        info = self.executor.get_device_info(device)
        assert info["serial"] == "abc123"
        assert info["platform"] == "android"
