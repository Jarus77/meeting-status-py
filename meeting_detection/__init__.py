"""
Python library for detecting active video meetings on macOS.

This library provides a simple API for detecting when video meetings are active,
with support for Zoom, Microsoft Teams, Google Meet, Cisco Webex, and more.

Example:
    ```python
    from meeting_detection import init, is_meeting_active, on_meeting_start, on_meeting_end

    # Initialize and start background polling
    init()

    # Register callbacks
    def handle_meeting_start(details):
        print(f"Meeting started: {details.app_name}")
        print(f"Reason: {details.reason}")

    def handle_meeting_end(details):
        print(f"Meeting ended")

    on_meeting_start(handle_meeting_start)
    on_meeting_end(handle_meeting_end)

    # Check current status
    if is_meeting_active():
        print("Currently in a meeting")
    ```
"""

import logging
from typing import Callable, Optional

from .engine import get_engine
from .models import DetectionDetails, SignalsBreakdown


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def init():
    """
    Initialize and start the meeting detection engine.

    Starts background polling every 2 seconds to detect meeting state changes.
    This must be called before using other functions.

    Example:
        ```python
        from meeting_detection import init
        init()
        ```

    Maps to init() in src/lib.rs lines 343-354
    """
    engine = get_engine()
    engine.start_polling()
    logging.getLogger(__name__).info("Meeting detection engine initialized and started")


def is_meeting_active() -> bool:
    """
    Check if a meeting is currently active.

    Returns:
        True if a meeting is detected as active, False otherwise

    Raises:
        RuntimeError: If init() has not been called

    Example:
        ```python
        from meeting_detection import init, is_meeting_active

        init()
        if is_meeting_active():
            print("In a meeting")
        ```

    Maps to is_meeting_active() in src/lib.rs lines 294-299
    """
    engine = get_engine()
    return engine.is_meeting_active()


def on_meeting_start(callback: Callable[[DetectionDetails], None]):
    """
    Register a callback for when a meeting starts.

    The callback will be called with DetectionDetails containing information
    about the detected meeting.

    Args:
        callback: Function to call when a meeting starts.
                  Receives DetectionDetails as argument.

    Raises:
        RuntimeError: If init() has not been called

    Example:
        ```python
        from meeting_detection import init, on_meeting_start

        def handle_start(details):
            print(f"Meeting started: {details.app_name}")
            print(f"Reason: {details.reason}")
            if details.meeting_url:
                print(f"URL: {details.meeting_url}")

        init()
        on_meeting_start(handle_start)
        ```

    Maps to on_meeting_start() in src/lib.rs lines 302-315
    """
    engine = get_engine()
    engine.add_start_callback(callback)


def on_meeting_end(callback: Callable[[DetectionDetails], None]):
    """
    Register a callback for when a meeting ends.

    The callback will be called with DetectionDetails from the last detection
    before the meeting ended.

    Args:
        callback: Function to call when a meeting ends.
                  Receives DetectionDetails as argument.

    Raises:
        RuntimeError: If init() has not been called

    Example:
        ```python
        from meeting_detection import init, on_meeting_end

        def handle_end(details):
            print(f"Meeting ended: {details.app_name}")

        init()
        on_meeting_end(handle_end)
        ```

    Maps to on_meeting_end() in src/lib.rs lines 318-331
    """
    engine = get_engine()
    engine.add_end_callback(callback)


def get_last_detection_details() -> Optional[DetectionDetails]:
    """
    Get details about the last detection cycle.

    This is useful for debugging and understanding why the engine thinks
    a meeting is active or not.

    Returns:
        DetectionDetails from the last detection cycle, or None if no
        detection has occurred yet

    Raises:
        RuntimeError: If init() has not been called

    Example:
        ```python
        from meeting_detection import init, get_last_detection_details

        init()
        details = get_last_detection_details()
        if details:
            print(f"Active: {details.active}")
            print(f"App: {details.app_name}")
            print(f"Reason: {details.reason}")
            print(f"Score: {details.score}")
        ```

    Maps to get_last_detection_details() in src/lib.rs lines 336-339
    """
    engine = get_engine()
    return engine.get_last_details()


# Public API exports
__all__ = [
    'init',
    'is_meeting_active',
    'on_meeting_start',
    'on_meeting_end',
    'get_last_detection_details',
    'DetectionDetails',
    'SignalsBreakdown',
]

__version__ = '1.0.0'
