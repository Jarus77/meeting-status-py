"""
Platform abstraction layer for meeting detection.

Provides platform-specific implementations for macOS.
"""

from .base import PlatformDetector
from .macos import MacOSDetector, get_browser_tab_urls, is_browser_process

__all__ = [
    'PlatformDetector',
    'MacOSDetector',
    'get_browser_tab_urls',
    'is_browser_process',
]
