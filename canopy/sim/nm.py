"""Network management (NM) helpers.

A real bus stays awake because ECUs exchange NM keep-alive frames (AUTOSAR NM / OSEK NM).
Without them, modules drop to sleep and the DUT never wakes. This provides a minimal,
generic NM frame good enough to hold the bus up; OEM-specific NM PDUs are added per
platform as needed (docs/ARCHITECTURE-NOTES.md §4).
"""

from __future__ import annotations

# AUTOSAR NM PDU layout (simplified): byte0 = source node id, byte1 = control bits.
NM_CONTROL_REPEAT_MESSAGE = 0x01
NM_CONTROL_ACTIVE_WAKEUP = 0x10


def nm_payload(
    source_node_id: int, *, control: int = NM_CONTROL_ACTIVE_WAKEUP, length: int = 8
) -> bytes:
    """Build a minimal NM keep-alive payload for a node."""
    data = bytearray(length)
    data[0] = source_node_id & 0xFF
    if length > 1:
        data[1] = control & 0xFF
    return bytes(data)
