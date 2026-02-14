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


def get_browser_tab_urls_generic(applescript_name: str) -> List[str]:
    """Get URLs from any browser using AppleScript. Works for all Chromium + Safari."""
    # Safety: verify app is running via System Events (prevents launching it)
    check_script = f'tell application "System Events" to (name of processes) contains "{applescript_name}"'
    try:
        check = subprocess.run(
            ['osascript', '-e', check_script],
            capture_output=True, text=True, timeout=3
        )
        if check.stdout.strip() != 'true':
            return []
    except Exception:
        return []

    # Extract tab URLs
    script = f'''
        tell application "{applescript_name}"
            set urlList to {{}}
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
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        urls_str = result.stdout.strip()
        return [s.strip() for s in urls_str.split(',') if s.strip()]
    except Exception:
        return []


def get_browser_tab_urls() -> Dict[str, List[str]]:
    """
    Get tab URLs from all running browsers in the registry.
    Returns dict of browser name -> list of URLs.
    """
    from ..config import BROWSER_REGISTRY

    browser_urls = {}

    # Collect running process names once
    running = set()
    for proc in psutil.process_iter(['name']):
        try:
            running.add(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for browser_name, applescript_name in BROWSER_REGISTRY.items():
        # Check if browser is in running processes (case-insensitive)
        is_running = any(
            browser_name.lower() in p.lower() or applescript_name.lower() in p.lower()
            for p in running
        )
        if is_running:
            urls = get_browser_tab_urls_generic(applescript_name)
            if urls:
                browser_urls[browser_name] = urls

    return browser_urls
