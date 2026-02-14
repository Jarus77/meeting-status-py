"""
Configuration for meeting detection.

This module defines meeting apps, URL patterns, and validation logic.
CRITICAL: Must match src/config.rs exactly for accuracy parity.
"""

import subprocess
from typing import List


# Meeting application process names (from src/config.rs lines 7-31)
MEETING_PROCESSES = [
    # Zoom
    "zoom",
    "zoom.us",
    "ZoomOpener",
    "zTsc",
    # Microsoft Teams
    "teams",
    "ms-teams",
    "Microsoft Teams",
    # Google Meet (runs in browser, but we check for Chrome/Edge with specific windows)
    "Google Chrome",
    "chrome",
    "Microsoft Edge",
    "msedge",
    # Webex
    "webexmta",
    "webex",
    "Cisco Webex",
    # Other common ones
    "skype",
    "Skype",
]


# Window title patterns that indicate a meeting (from src/config.rs lines 34-47)
MEETING_WINDOW_PATTERNS = [
    "meeting",
    "call",
    "conference",
    "webex",
    "zoom",
    "teams",
    "google meet",
    "hangouts",
    "video call",
    "audio call",
]


# Meeting URL patterns for browser-based meetings (from src/config.rs lines 50-82)
MEETING_URL_PATTERNS = [
    # Google Meet
    "meet.google.com/",

    # Microsoft Teams (web)
    "teams.live.com/v2/",
    "teams.live.com/light-meetings/launch",
    "teams.microsoft.com/_#/meet",
    "teams.microsoft.com/_#/conversations",

    # Zoom (web)
    "zoom.us/j/",
    "zoom.us/s/",
    "zoom.us/wc/",

    # Webex (web)
    "web.webex.com/meetings",
    ".webex.com/wbxmjs/joinservice",
    ".webex.com/webappng",
    "webex.com/webapp",
    "webex.com/meet",
    "meetings.webex.com",
]


# Comprehensive list of browser process names (from src/config.rs lines 192-242)
BROWSER_PROCESSES = [
    # Chromium-based browsers
    "Google Chrome",
    "chrome",
    "Chromium",
    "chromium",
    "Microsoft Edge",
    "msedge",
    "Edge",
    "Brave Browser",
    "brave",
    "Brave",
    "Opera",
    "opera",
    "Opera Browser",
    "Vivaldi",
    "vivaldi",
    "Yandex",
    "yandex",
    "Arc",
    "arc",
    # Firefox-based
    "Firefox",
    "firefox",
    "Firefox Developer Edition",
    "Firefox Nightly",
    # Safari
    "Safari",
    "safari",
    "Safari Technology Preview",
    # Other browsers
    "Tor Browser",
    "tor",
    "DuckDuckGo",
    "duckduckgo",
    "Epic Privacy Browser",
    "epic",
    "Maxthon",
    "maxthon",
    "Pale Moon",
    "palemoon",
    "Waterfox",
    "waterfox",
    "SeaMonkey",
    "seamonkey",
    # Electron-based browsers/apps
    "Electron",
    "electron",
]


# Browser registry for AppleScript URL extraction.
# Maps browser display names to AppleScript application names.
# All Chromium-based browsers share the same AppleScript tabs API.
# Safari also uses an identical API.
BROWSER_REGISTRY = {
    # Chromium-based
    'Google Chrome': 'Google Chrome',
    'Microsoft Edge': 'Microsoft Edge',
    'Arc': 'Arc',
    'Brave Browser': 'Brave Browser',
    'Opera': 'Opera',
    'Vivaldi': 'Vivaldi',
    'Chromium': 'Chromium',
    # Safari (same tabs API)
    'Safari': 'Safari',
    # Firefox omitted — no AppleScript tab URL support
}


def is_valid_google_meet_code(code: str) -> bool:
    """
    CRITICAL: Exact port of Rust logic from src/config.rs lines 95-132

    Validates Google Meet code format: xxx-yyyy-zzz

    Rules:
    - Exactly 3 segments separated by hyphens
    - Each segment: 2-5 lowercase letters only (a-z)
    - Total: 8-15 characters (excluding hyphens)

    Examples:
    - Valid: "abc-def-ghi" (3-3-3 = 9 chars)
    - Valid: "cih-fjjf-pfd" (3-4-3 = 10 chars)
    - Invalid: "abc-def" (only 2 segments)
    - Invalid: "ABC-def-ghi" (uppercase)
    - Invalid: "abc-d3f-ghi" (contains digit)
    """
    if not code:
        return False

    # Split by hyphens to get segments
    segments = code.split('-')

    # Must have exactly 3 segments
    if len(segments) != 3:
        return False

    # Each segment must:
    # 1. Be non-empty
    # 2. Contain only lowercase letters (a-z)
    # 3. Be between 2-5 characters
    for segment in segments:
        if not segment or len(segment) < 2 or len(segment) > 5:
            return False

        # Must be all lowercase letters
        if not segment.isalpha() or not segment.islower():
            return False

    # Total code length (excluding hyphens) should be reasonable
    total_chars = sum(len(s) for s in segments)
    if total_chars < 8 or total_chars > 15:
        return False

    return True


def is_meeting_url(url: str) -> bool:
    """
    CRITICAL: Exact port of Rust logic from src/config.rs lines 144-173

    Check if a URL matches any meeting pattern.

    Google Meet Detection:
    - Validates meeting code format (e.g., "cih-fjjf-pfd")
    - Excludes non-meeting pages: /landing, /new, /join, empty paths
    - Meeting codes: 3 segments, 2-5 chars each, lowercase letters, total 8-15 chars

    Other Services (Teams, Webex, Zoom web):
    - Uses pattern matching on URL strings
    """
    url_lower = url.lower()

    # Special handling for Google Meet: must have a valid meeting code
    if 'meet.google.com/' in url_lower:
        # Extract the path after meet.google.com/
        path_start = url_lower.find('meet.google.com/')
        if path_start == -1:
            return False

        after_domain = url_lower[path_start + len('meet.google.com/'):]

        # Extract path segment before query params (# or ?)
        path_segment = after_domain.split('?')[0].split('#')[0].rstrip('/')

        # Exclude non-meeting pages
        excluded_paths = ['landing', 'new', 'join', '']
        if path_segment in excluded_paths:
            return False

        # Validate if it's a proper meeting code
        return is_valid_google_meet_code(path_segment)

    # For other services, use simple pattern matching
    return any(pattern in url_lower for pattern in MEETING_URL_PATTERNS)


def is_meeting_process(process_name: str) -> bool:
    """
    Check if a process name matches any meeting app.
    From src/config.rs lines 176-181
    """
    process_lower = process_name.lower()
    return any(app.lower() in process_lower for app in MEETING_PROCESSES)


def is_meeting_window(window_title: str) -> bool:
    """
    Check if a window title matches any meeting pattern (fuzzy, case-insensitive).
    From src/config.rs lines 184-189
    """
    title_lower = window_title.lower()
    return any(pattern in title_lower for pattern in MEETING_WINDOW_PATTERNS)


def is_browser_process_pattern(process_name: str) -> bool:
    """
    Check if a process name matches any browser (pattern-based).
    From src/config.rs lines 245-250
    """
    process_lower = process_name.lower()
    return any(browser.lower() in process_lower for browser in BROWSER_PROCESSES)


def is_browser_process_macos(process_name: str) -> bool:
    """
    Check if a process is a browser on macOS using bundle categories.
    Uses mdls to check if the app's bundle category includes browser categories.
    From src/config.rs lines 254-404

    Returns True if the process is a browser, False otherwise.
    Falls back to pattern matching if bundle detection fails.
    """
    try:
        # First, try to find the app bundle path using AppleScript
        script = f'''
        tell application "System Events"
            try
                set appProcess to first process whose name is "{process_name}"
                set appPath to POSIX path of (file of appProcess as alias)
                return appPath
            on error
                return ""
            end try
        end tell
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0 or not result.stdout.strip():
            # Fall back to pattern matching if we can't get the path
            return is_browser_process_pattern(process_name)

        app_path = result.stdout.strip()

        # Try to get app store category type (most reliable for browsers)
        try:
            category_result = subprocess.run(
                ['mdls', '-name', 'kMDItemAppStoreCategoryType', app_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if category_result.returncode == 0:
                output_str = category_result.stdout

                # Parse mdls output: "kMDItemAppStoreCategoryType = "value"" or "(null)"
                if '=' in output_str:
                    category_value = output_str.split('=', 1)[1].strip().strip('"')
                    category_lower = category_value.lower()

                    # Check for browser-related categories
                    browser_category_patterns = ['web-browser', 'web-browsers', 'browser']
                    if category_value != '(null)' and category_value:
                        if any(pattern in category_lower for pattern in browser_category_patterns):
                            return True
        except:
            pass

        # Also check the human-readable category name
        try:
            category_name_result = subprocess.run(
                ['mdls', '-name', 'kMDItemAppStoreCategory', app_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if category_name_result.returncode == 0:
                output_str = category_name_result.stdout

                if '=' in output_str:
                    category_name = output_str.split('=', 1)[1].strip().strip('"')
                    category_lower = category_name.lower()

                    if category_name != '(null)' and category_name:
                        if 'browser' in category_lower or 'web' in category_lower:
                            return True
        except:
            pass

        # Check bundle identifier as fallback
        try:
            bundle_id_result = subprocess.run(
                ['mdls', '-name', 'kMDItemCFBundleIdentifier', app_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if bundle_id_result.returncode == 0:
                output_str = bundle_id_result.stdout

                if '=' in output_str:
                    bundle_id = output_str.split('=', 1)[1].strip().strip('"')
                    bundle_id_lower = bundle_id.lower()

                    browser_bundle_ids = [
                        'com.google.chrome',
                        'com.microsoft.edgemac',
                        'com.brave.browser',
                        'com.operasoftware.opera',
                        'com.vivaldi.vivaldi',
                        'org.mozilla.firefox',
                        'com.apple.safari',
                        'org.torproject.torbrowser',
                        'com.duckduckgo.mac.browser',
                        'com.epicbrowser.epic',
                    ]

                    if any(bid in bundle_id_lower for bid in browser_bundle_ids):
                        return True
        except:
            pass

        # Fall back to pattern matching if bundle detection fails
        return is_browser_process_pattern(process_name)

    except Exception:
        # If anything fails, fall back to pattern matching
        return is_browser_process_pattern(process_name)


def is_browser_process(process_name: str) -> bool:
    """
    Check if a process is a browser.
    Uses macOS-specific detection first, falls back to pattern matching.
    """
    return is_browser_process_macos(process_name)
