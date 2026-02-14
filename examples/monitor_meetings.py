#!/usr/bin/env python3
"""
Event-based meeting monitoring example.

This example demonstrates using callbacks to respond to meeting state changes.
"""

import time
from datetime import datetime
from meeting_detection import init, on_meeting_start, on_meeting_end


def handle_meeting_start(details):
    """Called when a meeting starts."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 🎥 Meeting started!")
    print(f"  App: {details.app_name}")
    print(f"  Reason: {details.reason}")

    if details.meeting_url:
        print(f"  URL: {details.meeting_url}")

    print(f"  Score: {details.score}")
    print(f"  Microphone: {details.signals.microphone.active}")
    print(f"  Camera: {details.signals.camera.active}")


def handle_meeting_end(details):
    """Called when a meeting ends."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 👋 Meeting ended!")
    print(f"  App: {details.app_name}")


def main():
    """Event-based monitoring example."""
    print("Meeting Detection Monitor")
    print("=" * 40)
    print("This example monitors for meeting state changes.")
    print("Join or leave a meeting to see events.\n")

    # Initialize the detection engine
    init()

    # Register callbacks
    on_meeting_start(handle_meeting_start)
    on_meeting_end(handle_meeting_end)

    print("Monitoring for meetings... (Press Ctrl+C to stop)\n")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped monitoring.")


if __name__ == '__main__':
    main()
