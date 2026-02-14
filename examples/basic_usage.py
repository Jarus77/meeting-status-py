#!/usr/bin/env python3
"""
Basic usage example for meeting-detection library.

This example demonstrates the simplest way to use the library to detect meetings.
"""

import time
from meeting_detection import init, is_meeting_active, get_last_detection_details


def main():
    """Basic usage example."""
    print("Initializing meeting detection...")
    init()

    print("Checking meeting status every 5 seconds...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Check if a meeting is currently active
            active = is_meeting_active()

            if active:
                # Get detailed information about the detection
                details = get_last_detection_details()

                if details:
                    print(f"✓ Meeting detected!")
                    print(f"  App: {details.app_name}")
                    print(f"  Reason: {details.reason}")
                    print(f"  Score: {details.score}")

                    if details.meeting_url:
                        print(f"  URL: {details.meeting_url}")

                    # Show signal breakdown
                    print(f"  Signals:")
                    print(f"    - Meeting app: {details.signals.meeting_app.active}")
                    print(f"    - Microphone: {details.signals.microphone.active}")
                    print(f"    - Camera: {details.signals.camera.active}")
                    print()
            else:
                print("✗ No meeting detected")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopped monitoring.")


if __name__ == '__main__':
    main()
