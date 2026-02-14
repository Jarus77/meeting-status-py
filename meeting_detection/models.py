"""
Data models for meeting detection library.

These models mirror the Rust structs from src/lib.rs and src/detector.rs
to ensure exact API compatibility.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# Score weights - must match JS constants in lib.rs lines 24-27
SCORE_MEETING_APP = 3
SCORE_MEETING_WINDOW = 2
SCORE_MICROPHONE = 2
SCORE_CAMERA = 1


class MeetingState(Enum):
    """State of meeting detection (from src/detector.rs lines 11-15)"""
    INACTIVE = "Inactive"
    ACTIVE = "Active"


class DetectionReason(Enum):
    """Reason for meeting detection decision (from src/detector.rs lines 18-26)"""
    NATIVE_APP_WITH_NETWORK = "native_app_with_network"
    BROWSER_WITH_MEETING_URL = "browser_with_meeting_url"
    NONE = "none"


@dataclass
class SignalDetails:
    """
    Signal information with active status and weight.
    Maps to src/lib.rs lines 39-42
    """
    active: bool
    weight: int


@dataclass
class SignalsBreakdown:
    """
    Breakdown of all detection signals.
    Maps to src/lib.rs lines 44-51
    """
    meeting_app: SignalDetails
    meeting_window: SignalDetails
    microphone: SignalDetails
    camera: SignalDetails


@dataclass
class DetectionDetails:
    """
    Detection details exposed to users via callbacks and API.
    Maps to JsDetectionDetails in src/lib.rs lines 54-62

    This is the public-facing API that users interact with.
    """
    active: bool
    score: int
    app_name: Optional[str]
    reason: str  # Format: "NativeAppWithNetwork(Zoom)" or "BrowserWithMeetingUrl(Safari)"
    meeting_url: Optional[str]
    signals: SignalsBreakdown

    @classmethod
    def from_detection_result(cls, result: 'DetectionResult') -> 'DetectionDetails':
        """
        Convert internal DetectionResult to public-facing DetectionDetails.
        Maps to detection_result_to_js() in src/lib.rs lines 64-118
        """
        # Calculate score for backward compatibility (not used in decision logic)
        score = 0
        if result.meeting_app_detected:
            score += SCORE_MEETING_APP
        if result.meeting_window_detected:
            score += SCORE_MEETING_WINDOW
        if result.microphone_active:
            score += SCORE_MICROPHONE
        if result.camera_active:
            score += SCORE_CAMERA

        # Convert reason to string format and extract meeting URL
        if result.reason == DetectionReason.NATIVE_APP_WITH_NETWORK:
            reason_str = f"NativeAppWithNetwork({result.reason_app_name or 'Unknown'})"
            meeting_url = None
        elif result.reason == DetectionReason.BROWSER_WITH_MEETING_URL:
            reason_str = f"BrowserWithMeetingUrl({result.reason_browser_name or 'Unknown'})"
            meeting_url = result.reason_url
        else:
            reason_str = "None"
            meeting_url = None

        return cls(
            active=result.is_meeting_active,
            score=score,
            app_name=result.meeting_app_name,
            reason=reason_str,
            meeting_url=meeting_url,
            signals=SignalsBreakdown(
                meeting_app=SignalDetails(
                    active=result.meeting_app_detected,
                    weight=SCORE_MEETING_APP
                ),
                meeting_window=SignalDetails(
                    active=result.meeting_window_detected,
                    weight=SCORE_MEETING_WINDOW
                ),
                microphone=SignalDetails(
                    active=result.microphone_active,
                    weight=SCORE_MICROPHONE
                ),
                camera=SignalDetails(
                    active=result.camera_active,
                    weight=SCORE_CAMERA
                ),
            )
        )


@dataclass
class DetectionResult:
    """
    Internal detection result with detailed breakdown.
    Maps to DetectionResult in src/detector.rs lines 29-39

    This is the internal representation used by the detection algorithm.
    """
    meeting_app_detected: bool
    meeting_app_name: Optional[str]
    meeting_window_detected: bool
    microphone_active: bool
    camera_active: bool
    score: int  # Kept for backward compatibility, not used in decision
    is_meeting_active: bool
    reason: DetectionReason

    # Additional fields to store reason details
    reason_app_name: Optional[str] = None
    reason_browser_name: Optional[str] = None
    reason_url: Optional[str] = None

    @staticmethod
    def create_inactive() -> 'DetectionResult':
        """Create a result indicating no meeting detected."""
        return DetectionResult(
            meeting_app_detected=False,
            meeting_app_name=None,
            meeting_window_detected=False,
            microphone_active=False,
            camera_active=False,
            score=0,
            is_meeting_active=False,
            reason=DetectionReason.NONE,
        )

    @staticmethod
    def create_native_app(app_name: str, microphone: bool = False, camera: bool = False) -> 'DetectionResult':
        """Create a result for native app with network activity."""
        return DetectionResult(
            meeting_app_detected=True,
            meeting_app_name=app_name,
            meeting_window_detected=False,
            microphone_active=microphone,
            camera_active=camera,
            score=SCORE_MEETING_APP + (SCORE_MICROPHONE if microphone else 0) + (SCORE_CAMERA if camera else 0),
            is_meeting_active=True,
            reason=DetectionReason.NATIVE_APP_WITH_NETWORK,
            reason_app_name=app_name,
        )

    @staticmethod
    def create_browser_meeting(browser_name: str, url: str, microphone: bool = False, camera: bool = False) -> 'DetectionResult':
        """Create a result for browser-based meeting."""
        return DetectionResult(
            meeting_app_detected=True,
            meeting_app_name=browser_name,
            meeting_window_detected=False,
            microphone_active=microphone,
            camera_active=camera,
            score=SCORE_MEETING_APP + (SCORE_MICROPHONE if microphone else 0) + (SCORE_CAMERA if camera else 0),
            is_meeting_active=True,
            reason=DetectionReason.BROWSER_WITH_MEETING_URL,
            reason_browser_name=browser_name,
            reason_url=url,
        )


class MeetingEvent(Enum):
    """Event types for internal engine (from src/lib.rs lines 31-34)"""
    STARTED = "Started"
    ENDED = "Ended"
