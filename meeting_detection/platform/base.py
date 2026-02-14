"""
Base platform detector interface.

Defines the abstract interface for platform-specific implementations.
Maps to PlatformDetector trait in src/platform/mod.rs lines 8-20
"""

from abc import ABC, abstractmethod
from typing import List


class PlatformDetector(ABC):
    """
    Platform-specific implementation interface for meeting detection.
    """

    @abstractmethod
    def is_microphone_active(self) -> bool:
        """Check if microphone is currently in use."""
        pass

    @abstractmethod
    def is_camera_active(self) -> bool:
        """Check if camera is currently in use."""
        pass

    @abstractmethod
    def get_running_processes(self) -> List[str]:
        """Get list of running process names."""
        pass

    @abstractmethod
    def get_visible_windows(self) -> List[str]:
        """Get list of visible window titles."""
        pass
