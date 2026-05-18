from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseExecutor(ABC):
    """Abstract base class for all test executors."""
    
    @abstractmethod
    def run(self, test_case: Any, device: Any, project: Any = None) -> Dict:
        """
        Execute a test case on a device.
        
        Args:
            test_case: The test case to execute
            device: The target device
            project: Optional project context
            
        Returns:
            Dict with keys: status, steps, logs, screenshots, error
        """
        pass
    
    @abstractmethod
    def get_device_info(self, device: Any) -> Dict:
        """Get device information."""
        pass
