"""Tests for TaskDispatcher."""
import pytest
from unittest.mock import MagicMock, patch
from core.task_dispatcher import TaskDispatcher
from models.test_task import TestTask
from models.test_case import TestCase
from models.device import Device


class TestTaskDispatcher:
    """Test TaskDispatcher."""

    def setup_method(self):
        self.dispatcher = TaskDispatcher()

    def test_dispatcher_init(self):
        """Test TaskDispatcher initialization."""
        assert "android" in self.dispatcher.executors
        assert "script" in self.dispatcher.executors
        assert isinstance(self.dispatcher.executors["android"], object)
        assert isinstance(self.dispatcher.executors["script"], object)

    def test_dispatch_task_not_found(self):
        """Test dispatch with non-existent task."""
        with patch("core.task_dispatcher.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_session.return_value = mock_db

            result = self.dispatcher.dispatch("nonexistent_task")
            assert result["status"] == "failed"
            assert "not found" in result["error"]

    def test_dispatch_test_case_not_found(self):
        """Test dispatch when test case not found."""
        with patch("core.task_dispatcher.SessionLocal") as mock_session:
            mock_db = MagicMock()
            # Task exists but case doesn't
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                TestTask(id="task_1", case_id="case_1", device_ids='["dev1"]'),
                None,  # Test case not found
            ]
            mock_session.return_value = mock_db

            result = self.dispatcher.dispatch("task_1")
            assert result["status"] == "failed"
            assert "Test case not found" in result["error"]
