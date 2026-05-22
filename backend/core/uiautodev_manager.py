"""uiautodev manager for device debugging."""
import subprocess
import time
import requests
from typing import Dict, Optional

class UiautodevManager:
    """Manages uiautodev server lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 20242):
        self.host = host
        self.port = port
        self.process = None
        self.server_url = f"http://{host}:{port}"

    def start(self) -> bool:
        """Start uiautodev server."""
        try:
            import sys
            cmd = ["uiauto.dev.exe" if sys.platform == "win32" else "uiauto.dev",
                   "server", "--no-browser", "--port", str(self.port)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Wait for server to start
            time.sleep(3)
            return self.is_running()
        except Exception as e:
            print(f"Failed to start uiautodev: {e}")
            return False

    def stop(self) -> bool:
        """Stop uiautodev server."""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
            return True
        except Exception as e:
            print(f"Failed to stop uiautodev: {e}")
            return False

    def is_running(self) -> bool:
        """Check if uiautodev server is running."""
        try:
            response = requests.get(f"{self.server_url}/", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_status(self) -> Dict:
        """Get uiautodev server status."""
        return {
            "running": self.is_running(),
            "url": self.server_url,
            "host": self.host,
            "port": self.port,
        }

    def get_device_url(self, device_serial: str) -> str:
        """Get device-specific URL for debugging."""
        return f"{self.server_url}/android/{device_serial}"

# Global instance
uiautodev_manager = UiautodevManager(port=20243)
