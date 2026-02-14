"""
Background polling engine with callbacks.

Implements 2-second polling with state change detection and callback execution.
Maps to DetectionEngine in src/lib.rs lines 121-273
"""

import asyncio
import logging
import threading
from typing import Callable, List, Optional

from .detector import MeetingDetector
from .models import DetectionDetails, DetectionResult, MeetingEvent, MeetingState


logger = logging.getLogger(__name__)


class DetectionEngine:
    """
    Background polling engine that runs detection every 2 seconds.
    Maps to DetectionEngine in src/lib.rs lines 121-273
    """

    def __init__(self):
        """Initialize the detection engine."""
        self.detector = MeetingDetector()
        self._start_callbacks: List[Callable[[DetectionDetails], None]] = []
        self._end_callbacks: List[Callable[[DetectionDetails], None]] = []
        self._last_result: Optional[DetectionResult] = None
        self._is_running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._callback_lock = threading.Lock()
        self._result_lock = threading.Lock()

    def start_polling(self):
        """
        Start background polling thread.
        From src/lib.rs lines 192-246
        """
        if self._is_running:
            return  # Already running

        self._is_running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        """Run async event loop in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._poll_loop())
        finally:
            self._loop.close()

    async def _poll_loop(self):
        """
        Poll every 2 seconds and trigger callbacks on state changes.
        From src/lib.rs lines 204-245

        Detects state changes (INACTIVE -> ACTIVE or ACTIVE -> INACTIVE)
        and triggers appropriate callbacks.
        """
        while self._is_running:
            try:
                # Perform detection with state tracking
                result, state_change = self.detector.detect_with_state()

                # Store last detection result BEFORE sending event
                with self._result_lock:
                    self._last_result = result

                # Trigger callbacks if state changed
                if state_change == MeetingState.ACTIVE:
                    app_name = result.meeting_app_name or "unknown"
                    reason_str = self._get_reason_str(result)
                    logger.info(f"Meeting started: {app_name} ({reason_str})")
                    self._trigger_callbacks(self._start_callbacks, result)

                elif state_change == MeetingState.INACTIVE:
                    app_name = result.meeting_app_name or "none"
                    logger.info(f"Meeting ended: {app_name}")
                    self._trigger_callbacks(self._end_callbacks, result)

            except Exception as e:
                logger.error(f"Detection error: {e}")

            # Wait 2 seconds before next poll
            await asyncio.sleep(2)

    def _get_reason_str(self, result: DetectionResult) -> str:
        """Extract reason string from detection result."""
        if result.reason_app_name:
            return "NativeAppWithNetwork"
        elif result.reason_browser_name:
            return "BrowserWithMeetingUrl"
        else:
            return "None"

    def _trigger_callbacks(self, callbacks: List[Callable], result: DetectionResult):
        """
        Execute callbacks in separate threads.
        From src/lib.rs lines 164-186

        Callbacks are executed in separate threads to prevent blocking
        the detection loop.
        """
        # Convert internal result to public-facing details
        details = DetectionDetails.from_detection_result(result)

        with self._callback_lock:
            callback_list = callbacks.copy()

        # Execute each callback in a separate thread
        for callback in callback_list:
            thread = threading.Thread(
                target=self._safe_callback_wrapper,
                args=(callback, details),
                daemon=True
            )
            thread.start()

    def _safe_callback_wrapper(self, callback: Callable, details: DetectionDetails):
        """Wrapper to catch and log callback exceptions."""
        try:
            callback(details)
        except Exception as e:
            logger.error(f"Callback error: {e}")

    def stop_polling(self):
        """
        Stop the polling loop.
        From src/lib.rs lines 248-250
        """
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def is_meeting_active(self) -> bool:
        """
        Check if a meeting is currently active.
        From src/lib.rs lines 252-257

        Returns:
            True if meeting is active, False otherwise
        """
        state = self.detector.get_current_state()
        return state == MeetingState.ACTIVE

    def add_start_callback(self, callback: Callable[[DetectionDetails], None]):
        """
        Register a callback for when a meeting starts.
        From src/lib.rs lines 259-262

        Args:
            callback: Function to call with DetectionDetails when meeting starts
        """
        with self._callback_lock:
            self._start_callbacks.append(callback)

    def add_end_callback(self, callback: Callable[[DetectionDetails], None]):
        """
        Register a callback for when a meeting ends.
        From src/lib.rs lines 264-267

        Args:
            callback: Function to call with DetectionDetails when meeting ends
        """
        with self._callback_lock:
            self._end_callbacks.append(callback)

    def get_last_details(self) -> Optional[DetectionDetails]:
        """
        Get details about the last detection cycle.
        From src/lib.rs lines 269-272

        Returns:
            DetectionDetails from last detection, or None if no detection yet
        """
        with self._result_lock:
            if self._last_result is None:
                return None
            return DetectionDetails.from_detection_result(self._last_result)


# Global engine instance (singleton pattern)
# From src/lib.rs lines 276-288
_engine: Optional[DetectionEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> DetectionEngine:
    """
    Get or create the global detection engine instance.

    Returns:
        Global DetectionEngine instance

    Raises:
        RuntimeError: If engine creation fails
    """
    global _engine

    with _engine_lock:
        if _engine is None:
            _engine = DetectionEngine()

        return _engine
