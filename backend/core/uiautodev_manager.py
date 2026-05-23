"""uiautodev manager for device debugging."""
import sys
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
            import shutil
            exe_name = "uiauto.dev.exe" if sys.platform == "win32" else "uiauto.dev"
            if shutil.which(exe_name):
                cmd = [exe_name, "server", "--no-browser", "--host", "127.0.0.1", "--port", str(self.port)]
            else:
                cmd = [sys.executable, "-m", "uiautodev", "--no-browser", "--host", "127.0.0.1", "--port", str(self.port)]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(3)
            return self.is_running()
        except Exception as e:
            print(f"Failed to start uiautodev: {e}")
            return False

    def stop(self) -> bool:
        """Stop uiautodev server and kill all uiauto* processes."""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
        except Exception as e:
            print(f"Failed to terminate process: {e}")

        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", "uiauto*"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "uiauto"], capture_output=True)
            return True
        except Exception as e:
            print(f"Failed to kill uiauto processes: {e}")
            return False

    def restart(self) -> bool:
        """Restart uiautodev server."""
        self.stop()
        time.sleep(1)
        return self.start()

    def is_running(self) -> bool:
        """Check if uiautodev server is running."""
        health_paths = ["/", "/status", "/health", ""]
        for path in health_paths:
            try:
                url = f"{self.server_url}{path}"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    return True
            except:
                continue
        for i in range(3):
            try:
                response = requests.get(f"{self.server_url}/", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                time.sleep(1)
        return False

    def get_status(self) -> Dict:
        """Get uiautodev server status."""
        return {
            "running": self.is_running(),
            "url": "https://uiauto2.devsleep.com",
            "host": self.host,
            "port": self.port,
        }

    def get_device_url(self, device_serial: str, platform: str = "android") -> str:
        """Get device-specific URL for debugging."""
        return f"https://uiauto2.devsleep.com/{platform}/{device_serial}"

# Global instance
uiautodev_manager = UiautodevManager(port=20243)
