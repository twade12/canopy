"""ISO-TP (ISO 15765-2) helpers — multi-frame transport under UDS/OBD.

Thin factory around :mod:`can-isotp` so the UDS client and the simulator's UDS server build
their transport stacks the same way. See CLAUDE.md §4.
"""

from __future__ import annotations

import isotp

# Conventional 11-bit diagnostic addressing (e.g. powertrain): tester 0x7E0 / ECU 0x7E8.
DEFAULT_TESTER_REQUEST_ID = 0x7E0
DEFAULT_TESTER_RESPONSE_ID = 0x7E8


def normal_11bit_address(request_id: int, response_id: int) -> isotp.Address:
    """Build a normal 11-bit ISO-TP address from the tester's point of view."""
    return isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        txid=request_id,
        rxid=response_id,
    )


def make_can_stack(bus, request_id: int, response_id: int) -> isotp.CanStack:
    """Create an ISO-TP stack on `bus` for the tester (tx=request, rx=response)."""
    return isotp.CanStack(bus=bus, address=normal_11bit_address(request_id, response_id))
