"""
Network connection detection for meeting apps.

CRITICAL: Must match src/network.rs exactly for accuracy parity.
Uses lsof to detect active network connections indicating meetings.
"""

import subprocess
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class NetworkConnection:
    """
    Network connection information.
    Maps to NetworkConnection in src/network.rs lines 8-14
    """
    process_name: str
    protocol: str  # "TCP", "UDP", "UNKNOWN"
    remote_address: str
    remote_port: int
    state: str  # "ESTABLISHED", "LISTEN", "CLOSED", "UNKNOWN"


# Meeting service domain patterns (from src/network.rs lines 17-32)
MEETING_DOMAINS = [
    # Zoom
    "zoom.us",
    "zoom.com",
    # Teams
    "teams.microsoft.com",
    "office.com",
    # Webex
    "webex.com",
    "cisco.com",
    # Google Meet
    "meet.google.com",
    "google.com",  # Too broad, but filtered by port/context
]


# Meeting service ports for video/audio streaming (from src/network.rs lines 35-48)
MEETING_VIDEO_PORTS = [
    8801,    # Zoom UDP video/audio
    8802,    # Zoom alternative
    3478,    # STUN (Teams, Webex)
    3479,    # STUN alternative
    3480,    # STUN alternative
    3481,    # STUN alternative
    9000,    # Webex video range start
    9999,    # Webex video range end
    19302,   # Google Meet UDP range start
    19309,   # Google Meet UDP range end
]


def parse_connection_name(name: str) -> Tuple[str, int, str]:
    """
    Parse connection name field from lsof output.
    From src/network.rs lines 93-131

    Examples:
    - "localhost:58660->localhost:10011 (ESTABLISHED)"
    - "10.0.0.199:53127->144-195-35.zoom.us:8801"
    - "144-195-35.zoom.us:8801"

    Returns: (remote_address, remote_port, state)
    """
    # Extract state if present
    if "ESTABLISHED" in name:
        state = "ESTABLISHED"
    elif "LISTEN" in name:
        state = "LISTEN"
    elif "CLOSED" in name:
        state = "CLOSED"
    else:
        state = "UNKNOWN"

    # Extract remote address and port
    # Look for pattern: ->remote:port or remote:port
    if "->" in name:
        # Format: local->remote:port
        arrow_pos = name.find("->")
        remote_part = name[arrow_pos + 2:]

        if ":" in remote_part:
            colon_pos = remote_part.find(":")
            address = remote_part[:colon_pos]
            port_str = remote_part[colon_pos + 1:].split()[0]
            try:
                port = int(port_str)
            except ValueError:
                port = 0
            return (address, port, state)
    elif ":" in name:
        # Format: remote:port (no arrow)
        colon_pos = name.find(":")
        address = name[:colon_pos]
        port_str = name[colon_pos + 1:].split()[0]
        try:
            port = int(port_str)
        except ValueError:
            port = 0
        return (address, port, state)

    return ("", 0, state)


def parse_lsof_output(output: str) -> List[NetworkConnection]:
    """
    Parse lsof output to extract network connections.
    From src/network.rs lines 51-86

    lsof format:
    COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
    """
    connections = []

    for line in output.splitlines():
        # Skip header line and empty lines
        if line.startswith("COMMAND") or not line.strip():
            continue

        # Parse lsof format
        parts = line.split()
        if len(parts) < 9:
            continue

        process_name = parts[0]

        # Determine protocol
        if "TCP" in line:
            protocol = "TCP"
        elif "UDP" in line:
            protocol = "UDP"
        else:
            protocol = "UNKNOWN"

        # Extract remote address and port from NAME field (last field)
        name_field = " ".join(parts[8:])

        # Parse connection info
        remote_address, remote_port, state = parse_connection_name(name_field)

        connections.append(NetworkConnection(
            process_name=process_name,
            protocol=protocol,
            remote_address=remote_address,
            remote_port=remote_port,
            state=state,
        ))

    return connections


def get_network_connections_for_process(process_name: str) -> List[NetworkConnection]:
    """
    Get network connections for a specific process.
    From src/network.rs lines 134-160

    Uses lsof -i -P -n to get network connections.
    Raises RuntimeError if lsof command fails.
    """
    try:
        result = subprocess.run(
            ['lsof', '-i', '-P', '-n'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            raise RuntimeError("Failed to get network connections via lsof")

        all_connections = parse_lsof_output(result.stdout)

        # Filter for the specific process (exact match)
        process_connections = [
            conn for conn in all_connections
            if conn.process_name == process_name
        ]

        return process_connections

    except subprocess.TimeoutExpired:
        raise RuntimeError("lsof command timed out")
    except FileNotFoundError:
        raise RuntimeError("lsof command not found (macOS required)")


def detect_meeting_network_activity(process_name: str) -> Tuple[bool, int, List[str]]:
    """
    CRITICAL: Exact port of Rust logic from src/network.rs lines 169-218

    Check if network connections indicate an active meeting.

    App-specific detection logic:
    - Zoom: UDP port 8801 is a strong indicator (works with IP addresses)
    - Teams/Webex: STUN ports (3478-3481) or meeting domains with ESTABLISHED
    - Google Meet: Meeting domains with ESTABLISHED or video ports (19302-19309)

    Returns: (has_meeting_connections, connection_count, details)
    """
    connections = get_network_connections_for_process(process_name)

    meeting_connections = []
    details = []

    for conn in connections:
        # Check if connection is to a meeting domain
        is_meeting_domain = any(
            domain in conn.remote_address
            for domain in MEETING_DOMAINS
        )

        # Check if connection is on a video/audio port
        is_video_port = conn.remote_port in MEETING_VIDEO_PORTS

        # Check if connection is established (active)
        is_established = conn.state == "ESTABLISHED"

        # Zoom-specific: UDP port 8801 is a strong indicator
        # UDP connections often show "UNKNOWN" state, so we check the port
        # But only if it's a recent/active connection (not CLOSED)
        is_zoom_udp = (
            conn.protocol == "UDP" and
            conn.remote_port == 8801 and
            conn.state != "CLOSED"
        )

        # Meeting connection if:
        # 1. Meeting domain AND ESTABLISHED (must be active, not just any state), OR
        # 2. Meeting domain AND video port (video ports indicate active streaming), OR
        # 3. Zoom UDP on port 8801 (Zoom-specific, but not if CLOSED)
        is_meeting_connection = (
            (is_meeting_domain and (is_established or is_video_port)) or
            is_zoom_udp
        )

        if is_meeting_connection:
            meeting_connections.append(conn)
            details.append(
                f"{conn.protocol} {conn.process_name} "
                f"{conn.remote_address}:{conn.remote_port} ({conn.state})"
            )

    has_meeting = len(meeting_connections) > 0
    return (has_meeting, len(meeting_connections), details)
