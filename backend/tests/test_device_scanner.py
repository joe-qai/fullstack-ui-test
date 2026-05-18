import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
from db.database import SessionLocal, engine
from models.base import Base
from core.device_scanner import DeviceScanner
from models.device import Device


class TestDeviceScanner:
    def setup_method(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.db.query(Device).delete()
        self.db.commit()

    def teardown_method(self):
        self.db.query(Device).delete()
        self.db.commit()
        self.db.close()

    def test_scan_devices_mock(self):
        mock_output = "List of devices attached\nabc123\tdevice\tproduct:pixel model:Pixel4 device:pixel4 transport_id:1\n"
        with patch("core.device_scanner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            devices = DeviceScanner.scan_devices()
            assert "abc123" in devices
            assert devices["abc123"]["model"] == "Pixel4"

    def test_sync_devices(self):
        mock_output = "List of devices attached\nabc123\tdevice\tproduct:pixel model:Pixel4\n"
        with patch("core.device_scanner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            DeviceScanner.sync_devices(self.db)

        devices = DeviceScanner.get_devices(self.db)
        assert len(devices) == 1
        assert devices[0].serial == "abc123"
        assert devices[0].status == "online"
