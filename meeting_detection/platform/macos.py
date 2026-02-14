"""
macOS-specific implementation for meeting detection.

Uses AppleScript for browser URL extraction and psutil for process management.
Maps to src/platform/macos.rs
"""

import psutil
import subprocess
from typing import Dict, List
from .base import PlatformDetector
from ..config import is_browser_process_macos


class MacOSDetector(PlatformDetector):
    """
    macOS-specific platform detector.
    Maps to MacOSDetector in src/platform/macos.rs lines 10-129
    """

    def __init__(self):
        """Initialize the macOS detector."""
        pass

    def is_microphone_active(self) -> bool:
        """
        Check if microphone is currently in use.
        From src/platform/macos.rs lines 23-39

        Note: For v1, this returns False. Proper CoreAudio detection
        can be added in future versions if needed.
        """
        # For v1 simplicity, return False
        # This allows the system to work but mic detection will need proper implementation
        return False

    def is_camera_active(self) -> bool:
        """
        Check if camera is currently in use.
        From src/platform/macos.rs lines 41-62

        Simplified v1: checks if common camera-using apps are running.
        """
        processes = self.get_running_processes()
        camera_keywords = ["zoom", "teams", "facetime", "photo booth", "quicktime"]

        has_camera_app = any(
            any(keyword in p.lower() for keyword in camera_keywords)
            for p in processes
        )

        return has_camera_app

    def get_running_processes(self) -> List[str]:
        """
        Get list of running process names.
        From src/platform/macos.rs lines 64-77
        """
        processes = []

        for proc in psutil.process_iter(['name']):
            try:
                processes.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def get_visible_windows(self) -> List[str]:
        """
        Get list of visible window titles using AppleScript.
        From src/platform/macos.rs lines 79-128
        """
        script = '''
            tell application "System Events"
                set windowList to {}
                repeat with proc in processes
                    try
                        set windowTitles to name of windows of proc
                        repeat with title in windowTitles
                            set end of windowList to title
                        end repeat
                    end try
                end repeat
                set AppleScript's text item delimiters to ", "
                set resultString to windowList as string
                set AppleScript's text item delimiters to ""
                return resultString
            end tell
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return []

            titles_str = result.stdout.strip()

            # Parse the AppleScript output (comma-separated)
            titles = [
                s.strip()
                for s in titles_str.split(',')
                if s.strip() and not s.strip().startswith('item 1 of')
            ]

            return titles

        except Exception:
            return []


def is_browser_process(process_name: str) -> bool:
    """
    Check if a process is a browser using macOS app categories.
    From src/platform/macos.rs lines 135-137
    """
    return is_browser_process_macos(process_name)


def get_browser_tab_urls() -> Dict[str, List[str]]:
    """
    Get browser tab URLs for meeting detection.
    Returns dict of browser name -> list of URLs.
    From src/platform/macos.rs lines 142-167
    """
    browser_urls = {}

    # Get URLs from Chrome
    chrome_urls = get_chrome_tab_urls()
    if chrome_urls:
        browser_urls['Google Chrome'] = chrome_urls

    # Get URLs from Safari
    safari_urls = get_safari_tab_urls()
    if safari_urls:
        browser_urls['Safari'] = safari_urls

    # Get URLs from Edge
    edge_urls = get_edge_tab_urls()
    if edge_urls:
        browser_urls['Microsoft Edge'] = edge_urls

    return browser_urls


def get_chrome_tab_urls() -> List[str]:
    """
    Get URLs from all Chrome tabs using AppleScript.
    From src/platform/macos.rs lines 170-207
    """
    script = '''
        tell application "Google Chrome"
            set urlList to {}
            repeat with w in windows
                repeat with t in tabs of w
                    set end of urlList to URL of t
                end repeat
            end repeat
            set AppleScript's text item delimiters to ", "
            set resultString to urlList as string
            set AppleScript's text item delimiters to ""
            return resultString
        end tell
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        urls_str = result.stdout.strip()

        # Parse comma-separated URLs
        urls = [
            s.strip()
            for s in urls_str.split(',')
            if s.strip()
        ]

        return urls

    except Exception:
        # Chrome not running or error - return empty
        return []


def get_safari_tab_urls() -> List[str]:
    """
    Get URLs from all Safari tabs using AppleScript.
    From src/platform/macos.rs lines 210-247
    """
    script = '''
        tell application "Safari"
            set urlList to {}
            repeat with w in windows
                repeat with t in tabs of w
                    set end of urlList to URL of t
                end repeat
            end repeat
            set AppleScript's text item delimiters to ", "
            set resultString to urlList as string
            set AppleScript's text item delimiters to ""
            return resultString
        end tell
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        urls_str = result.stdout.strip()

        # Parse comma-separated URLs
        urls = [
            s.strip()
            for s in urls_str.split(',')
            if s.strip()
        ]

        return urls

    except Exception:
        # Safari not running or error - return empty
        return []


def get_edge_tab_urls() -> List[str]:
    """
    Get URLs from all Edge tabs using AppleScript.
    From src/platform/macos.rs lines 250-287
    """
    script = '''
        tell application "Microsoft Edge"
            set urlList to {}
            repeat with w in windows
                repeat with t in tabs of w
                    set end of urlList to URL of t
                end repeat
            end repeat
            set AppleScript's text item delimiters to ", "
            set resultString to urlList as string
            set AppleScript's text item delimiters to ""
            return resultString
        end tell
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        urls_str = result.stdout.strip()

        # Parse comma-separated URLs
        urls = [
            s.strip()
            for s in urls_str.split(',')
            if s.strip()
        ]

        return urls

    except Exception:
        # Edge not running or error - return empty
        return []
