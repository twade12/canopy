"""Round-trip tests for the CAN interface against a virtual bus."""

from __future__ import annotations

from canopy.config import CanConfig
from canopy.hal import CanInterface


def test_send_receive_round_trip(can_config: CanConfig) -> None:
    """A frame sent on one interface is received on a second on the same channel."""
    with CanInterface(can_config) as tx, CanInterface(can_config) as rx:
        sent = tx.send(0x123, b"\x01\x02\x03\x04")
        received = rx.receive(timeout=2.0)

    assert received is not None
    assert received.arbitration_id == sent.arbitration_id == 0x123
    assert bytes(received.data) == b"\x01\x02\x03\x04"


def test_monitor_respects_limit(can_config: CanConfig) -> None:
    """monitor() stops after `limit` frames."""
    with CanInterface(can_config) as tx, CanInterface(can_config) as rx:
        for i in range(3):
            tx.send(0x200 + i, bytes([i]))
        frames = list(rx.monitor(timeout=2.0, limit=3))

    assert len(frames) == 3
    assert {f.arbitration_id for f in frames} == {0x200, 0x201, 0x202}


def test_monitor_stops_on_idle_timeout(can_config: CanConfig) -> None:
    """monitor() returns when the bus goes idle past the timeout."""
    with CanInterface(can_config) as rx:
        frames = list(rx.monitor(timeout=0.2))
    assert frames == []


def test_extended_id_round_trip(can_config: CanConfig) -> None:
    """29-bit identifiers survive the round trip."""
    with CanInterface(can_config) as tx, CanInterface(can_config) as rx:
        tx.send(0x18DAF110, b"\xaa", is_extended_id=True)
        received = rx.receive(timeout=2.0)

    assert received is not None
    assert received.is_extended_id
    assert received.arbitration_id == 0x18DAF110
