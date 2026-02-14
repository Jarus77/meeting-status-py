# Meeting Detection - Python Library

Python implementation of the meeting detection library for detecting active video meetings on macOS.

This is a pure Python port of the original Rust/Node.js implementation, maintaining 100% accuracy parity while being more accessible for command-line tools and Python scripts.

## Features

- ✅ Two-tier detection algorithm for accurate meeting detection
- ✅ Event-based API with callbacks (`on_meeting_start`, `on_meeting_end`)
- ✅ Simple Python API - no native compilation required
- ✅ Background polling every 2 seconds
- ✅ 100% accuracy parity with Rust implementation

## Supported Platforms & Services

| Service             | Native App | Browser | Detection Method                                                                                                             |
| ------------------- | ---------- | ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Zoom**            | ✅         | ✅      | Tier 1: Network connections (UDP port 8801)<br>Tier 2: URL patterns (`zoom.us/j/`, `zoom.us/s/`)                             |
| **Google Meet**     | ❌         | ✅      | Tier 2: URL patterns with meeting code validation (`meet.google.com/xxx-yyyy-zzz`)                                           |
| **Microsoft Teams** | ✅         | ✅      | Tier 1: Network connections (STUN/TURN ports)<br>Tier 2: URL patterns (`teams.live.com/v2/`, `teams.microsoft.com/_#/meet/`) |
| **Webex**           | ✅         | ✅      | Tier 1: Network connections (video ports)<br>Tier 2: URL patterns (`*.webex.com/webapp/`, `*.webex.com/meet/`)               |

**Supported Operating Systems:**

- **macOS** ✅ (Intel and Apple Silicon)

## Installation

### From PyPI

```bash
pip install meeting-detection
```

### From GitHub

```bash
pip install git+https://github.com/Jarus77/meeting-status-py.git
```

### For Development

```bash
git clone https://github.com/Jarus77/meeting-status-py.git
cd meeting-status-py
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- macOS (uses `lsof`, `osascript`, `mdls`)
- Dependencies: `psutil`, `typing-extensions`

## Usage

### Basic Example

```python
from meeting_detection import init, is_meeting_active, get_last_detection_details

# Initialize the engine (starts background polling every 2 seconds)
init()

# Check current status
active = is_meeting_active()
print(f"Meeting active: {active}")

# Get detailed detection information
details = get_last_detection_details()
if details:
    print(f"App: {details.app_name}")
    print(f"Reason: {details.reason}")
    if details.meeting_url:
        print(f"URL: {details.meeting_url}")
```

### Event-Based Monitoring

```python
import time
from meeting_detection import init, on_meeting_start, on_meeting_end

# Initialize the engine
init()

# Register callbacks
def handle_meeting_start(details):
    print(f"🎥 Meeting started!")
    print(f"  App: {details.app_name}")
    print(f"  Reason: {details.reason}")
    if details.meeting_url:
        print(f"  URL: {details.meeting_url}")

def handle_meeting_end(details):
    print(f"👋 Meeting ended!")
    print(f"  App: {details.app_name}")

on_meeting_start(handle_meeting_start)
on_meeting_end(handle_meeting_end)

# Keep the script running
print("Monitoring for meetings... (Press Ctrl+C to stop)")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped monitoring.")
```

### Command-Line Tool Example

```python
#!/usr/bin/env python3
"""Simple CLI tool to check meeting status."""

import sys
from meeting_detection import init, is_meeting_active

def main():
    init()

    # Wait for first detection cycle
    import time
    time.sleep(3)

    if is_meeting_active():
        print("In a meeting")
        sys.exit(0)
    else:
        print("Not in a meeting")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## API Reference

### Functions

#### `init()`

Initialize and start the meeting detection engine. Must be called before using other functions.

```python
init()
```

#### `is_meeting_active() -> bool`

Check if a meeting is currently active.

```python
active = is_meeting_active()
```

**Returns:** `True` if meeting is active, `False` otherwise

#### `on_meeting_start(callback: Callable[[DetectionDetails], None])`

Register a callback for when a meeting starts.

```python
def handle_start(details):
    print(f"Meeting started: {details.app_name}")

on_meeting_start(handle_start)
```

**Parameters:**
- `callback`: Function that receives `DetectionDetails` when a meeting starts

#### `on_meeting_end(callback: Callable[[DetectionDetails], None])`

Register a callback for when a meeting ends.

```python
def handle_end(details):
    print(f"Meeting ended: {details.app_name}")

on_meeting_end(handle_end)
```

**Parameters:**
- `callback`: Function that receives `DetectionDetails` when a meeting ends

#### `get_last_detection_details() -> Optional[DetectionDetails]`

Get details about the last detection cycle.

```python
details = get_last_detection_details()
if details:
    print(f"App: {details.app_name}")
    print(f"Active: {details.active}")
```

**Returns:** `DetectionDetails` or `None` if no detection has occurred yet

### Data Classes

#### `DetectionDetails`

Contains detailed information about meeting detection.

**Attributes:**
- `active` (bool): Whether a meeting is currently active
- `score` (int): Detection score (for backward compatibility)
- `app_name` (str | None): Name of the meeting application
- `reason` (str): Detection reason (e.g., "NativeAppWithNetwork(Zoom)")
- `meeting_url` (str | None): Meeting URL (for browser-based meetings)
- `signals` (SignalsBreakdown): Breakdown of detection signals

#### `SignalsBreakdown`

Breakdown of all detection signals.

**Attributes:**
- `meeting_app` (SignalDetails): Meeting app detection signal
- `meeting_window` (SignalDetails): Meeting window detection signal
- `microphone` (SignalDetails): Microphone active signal
- `camera` (SignalDetails): Camera active signal

#### `SignalDetails`

Information about a specific detection signal.

**Attributes:**
- `active` (bool): Whether this signal is active
- `weight` (int): Weight of this signal in the overall score

## How It Works

### Two-Tier Detection Algorithm

The library uses a two-tier detection algorithm to accurately identify active meetings:

#### Tier 1: Native Meeting Apps

For native apps (Zoom desktop, Teams desktop, Webex desktop), **network connections** are the primary signal:

- **Zoom**: UDP port 8801 is a strong indicator (works with IP addresses)
- **Teams/Webex**: STUN ports (3478-3481) or meeting domains with ESTABLISHED connections
- **Decision**: If network connections active → MEETING ACTIVE

#### Tier 2: Browser-Based Meetings

For browser-based meetings (Google Meet, Teams web, Webex web), **browser tab URLs** are definitive:

- **Google Meet**: Validates meeting code format (xxx-yyyy-zzz), excludes landing pages
- **Teams/Webex web**: Pattern matching on meeting URLs
- **Decision**: If meeting URL detected → MEETING ACTIVE

### Google Meet Code Validation

Google Meet URLs require special validation to avoid false positives:

- Format: `xxx-yyyy-zzz` (3 segments separated by hyphens)
- Each segment: 2-5 lowercase letters only
- Total: 8-15 characters (excluding hyphens)
- Excludes: `/landing`, `/new`, `/join`, empty paths

Example valid codes:
- `abc-def-ghi` ✅
- `cih-fjjf-pfd` ✅

Example invalid:
- `abc-def` ❌ (only 2 segments)
- `ABC-def-ghi` ❌ (uppercase)
- `abc-d3f-ghi` ❌ (contains digit)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=meeting_detection --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run manual validation
python tests/manual_test.py
```

### Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Event-based monitoring
python examples/monitor_meetings.py

# Manual validation
python tests/manual_test.py
```

### Project Structure

```
meeting_detection/
├── meeting_detection/        # Main package
│   ├── __init__.py          # Public API
│   ├── models.py            # Data models
│   ├── config.py            # Configuration and patterns
│   ├── network.py           # Network detection (lsof)
│   ├── detector.py          # Two-tier detection algorithm
│   ├── engine.py            # Background polling engine
│   └── platform/            # Platform-specific code
│       ├── base.py          # Abstract interface
│       └── macos.py         # macOS implementation
├── tests/                   # Unit tests
│   ├── test_config.py       # Config and validation tests
│   ├── test_network.py      # Network detection tests
│   └── test_detector.py     # Detection algorithm tests
├── examples/                # Usage examples
│   ├── basic_usage.py
│   └── monitor_meetings.py
└── requirements.txt         # Dependencies
```

## Accuracy Parity with Rust Implementation

This Python implementation is designed to maintain 100% accuracy parity with the original Rust implementation. Critical components that ensure this:

1. **Google Meet Validation** (`config.py:is_valid_google_meet_code`)
   - Exact port of Rust logic for meeting code validation
   - Prevents false positives from landing pages

2. **Network Detection** (`network.py:detect_meeting_network_activity`)
   - Zoom UDP port 8801 detection (works without domain matching)
   - Teams STUN ports (3478-3481)
   - Proper handling of connection states (ESTABLISHED, CLOSED, UNKNOWN)

3. **Two-Tier Algorithm** (`detector.py:detect`)
   - Native apps checked before browsers
   - Browsers skipped in Tier 1, handled in Tier 2
   - State transitions tracked correctly

## Troubleshooting

### Permissions

The library requires certain macOS permissions:

- **Terminal/Python**: May need accessibility permissions for `osascript`
- **Network Access**: Uses `lsof` to check network connections (no special permissions required)

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Get detailed detection information:

```python
details = get_last_detection_details()
if details:
    print(f"Active: {details.active}")
    print(f"Reason: {details.reason}")
    print(f"Score: {details.score}")
    print(f"Signals: {details.signals}")
```

## License

MIT

## Credits

This is a pure Python port of the original [meeting-detection](https://github.com/Ayobamiu/meeting-detection) library (Rust/Node.js implementation by [@Ayobamiu](https://github.com/Ayobamiu)). This Python version maintains 100% accuracy parity with the original implementation while providing a more accessible API for Python developers and command-line tools.

**Original Repository:** https://github.com/Ayobamiu/meeting-detection
