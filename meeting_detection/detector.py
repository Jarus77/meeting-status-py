"""
Core detection logic with two-tier detection algorithm.

CRITICAL: Must match src/detector.rs exactly for accuracy parity.

Two-tier detection strategy:
- Tier 1: Native apps (Zoom, Teams, Webex) - network connections primary signal
- Tier 2: Browser meetings (Google Meet, etc.) - browser tab URLs definitive
"""

import threading
from typing import Optional, Tuple

from .config import is_meeting_process, is_meeting_url
from .network import detect_meeting_network_activity
from .platform import MacOSDetector, get_browser_tab_urls, is_browser_process
from .models import DetectionResult, MeetingState


class MeetingDetector:
    """
    Main detector that combines all signals using two-tier algorithm.
    Maps to MeetingDetector in src/detector.rs lines 42-197
    """

    def __init__(self, platform: Optional[MacOSDetector] = None):
        """
        Initialize the meeting detector.

        Args:
            platform: Platform-specific detector. If None, creates MacOSDetector.
        """
        self.platform = platform if platform is not None else MacOSDetector()
        self._previous_state = MeetingState.INACTIVE
        self._state_lock = threading.Lock()

    def detect(self) -> DetectionResult:
        """
        Perform a detection cycle and return the result.
        From src/detector.rs lines 72-162

        Uses app-specific decision tree:

        **Tier 1: Native Meeting Apps (Zoom, Teams desktop, Webex desktop)**
        - Detection strategy: Network connections are the primary signal
        - Why: Native apps maintain persistent network connections when in a meeting
        - Zoom-specific: UDP port 8801 is a strong indicator
        - Teams/Webex: STUN ports (3478-3481) or meeting domains with ESTABLISHED
        - Decision: If network connections active → MEETING ACTIVE

        **Tier 2: Browser-based Meetings (Google Meet, Teams web, Webex web)**
        - Detection strategy: Browser tab URLs are definitive
        - Why: Network connections unreliable for browsers (mixed/encrypted traffic)
        - Google Meet: Validates meeting code format, excludes landing pages
        - Teams/Webex web: Pattern matching on meeting URLs
        - Decision: If meeting URL detected → MEETING ACTIVE

        Returns:
            DetectionResult with detection details
        """
        # Check microphone (for supporting info, not decision)
        try:
            microphone_active = self.platform.is_microphone_active()
        except Exception:
            microphone_active = False

        # Check camera (for supporting info, not decision)
        try:
            camera_active = self.platform.is_camera_active()
        except Exception:
            camera_active = False

        # Get running processes
        try:
            processes = self.platform.get_running_processes()
        except Exception:
            processes = []

        # Window detection disabled for performance (not used in decision tree)
        meeting_window_detected = False

        # TIER 1: Check for native meeting apps (Zoom, Teams desktop, Webex desktop)
        # For native apps, network connections are the primary signal
        for process_name in processes:
            if is_meeting_process(process_name):
                # Check if it's a browser first (browsers are handled in Tier 2)
                try:
                    if is_browser_process(process_name):
                        continue  # Skip browsers, handle in Tier 2
                except Exception:
                    pass

                # It's a native meeting app - check network connections
                try:
                    has_network, _count, _details = detect_meeting_network_activity(process_name)

                    if has_network:
                        # Native app with network activity = active meeting
                        return DetectionResult.create_native_app(
                            app_name=process_name,
                            microphone=microphone_active,
                            camera=camera_active
                        )
                except Exception:
                    # Network detection failed for this process, continue checking others
                    pass

                # No network connections = no active meeting for native apps

        # TIER 2: Check for browser-based meetings (Google Meet, Teams web, Webex web)
        # For browser-based meetings, meeting URLs are definitive
        try:
            browser_urls_map = get_browser_tab_urls()

            for browser_name, urls in browser_urls_map.items():
                for url in urls:
                    if is_meeting_url(url):
                        # Browser with meeting URL = active meeting
                        return DetectionResult.create_browser_meeting(
                            browser_name=browser_name,
                            url=url,
                            microphone=microphone_active,
                            camera=camera_active
                        )
        except Exception:
            # Browser URL detection failed
            pass

        # No meeting detected
        return DetectionResult.create_inactive()

    def detect_with_state(self) -> Tuple[DetectionResult, Optional[MeetingState]]:
        """
        Perform detection and also compute state change in one pass.
        From src/detector.rs lines 165-186

        Returns:
            Tuple of (DetectionResult, state_change)
            state_change is None if no change, or new MeetingState if changed
        """
        result = self.detect()

        new_state = MeetingState.ACTIVE if result.is_meeting_active else MeetingState.INACTIVE

        with self._state_lock:
            previous_state = self._previous_state

            if new_state != previous_state:
                self._previous_state = new_state
                state_change = new_state
            else:
                state_change = None

        return (result, state_change)

    def get_current_state(self) -> MeetingState:
        """
        Get current meeting state without triggering state change.
        From src/detector.rs lines 189-196

        Returns:
            Current MeetingState (ACTIVE or INACTIVE)
        """
        result = self.detect()
        return MeetingState.ACTIVE if result.is_meeting_active else MeetingState.INACTIVE
