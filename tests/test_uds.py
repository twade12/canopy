"""End-to-end UDS round-trip: the station's tester talks to a simulated ECU on (v)CAN.

This is the A1 ⇄ B2 validation from the battle plan: the udsoncan-based client and the
simulator's hand-rolled UDS server check each other for free over real ISO-TP (the 17-byte
VIN forces multi-frame segmentation + flow control).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from canopy.config import CanConfig
from canopy.hal.uds import UdsClient
from canopy.sim.uds_server import UdsServer, UdsServerConfig

VIN = "1FT7W2BT0GEA12345"


@pytest.fixture
def diag_channel(can_config: CanConfig) -> CanConfig:
    # ISO-TP must not receive its own frames, or the stack sees its own flow-control.
    return replace(can_config, receive_own_messages=False)


def test_uds_round_trip(diag_channel: CanConfig) -> None:
    server = UdsServer(
        diag_channel,
        request_id=0x7E0,
        response_id=0x7E8,
        config=UdsServerConfig(vin=VIN, dtcs=[(0x010100, 0x09), (0x008700, 0x08)]),
    )
    server.start()
    try:
        with UdsClient(channel=diag_channel, request_id=0x7E0, response_id=0x7E8) as uds:
            uds.change_session(1)
            uds.tester_present()

            assert uds.read_vin() == VIN                      # multi-frame ISO-TP

            codes = {d.code for d in uds.read_dtcs(0xFF)}
            assert codes == {0x010100, 0x008700}

            uds.clear_dtcs()
            assert uds.read_dtcs(0xFF) == []                  # cleared
    finally:
        server.stop()


def test_uds_actuation_round_trip(diag_channel: CanConfig) -> None:
    """The new control services (0x2F / 0x31 / 0x2E / 0x27) against the virtual ECU."""
    server = UdsServer(
        diag_channel, request_id=0x7E0, response_id=0x7E8, config=UdsServerConfig(vin=VIN))
    server.start()
    try:
        with UdsClient(channel=diag_channel, request_id=0x7E0, response_id=0x7E8) as uds:
            uds.change_session(3)

            io = uds.io_control(0x4A01, "short_term_adjust", b"\x01")   # actuate (0x2F)
            assert io.positive and io.service == 0x2F

            routine = uds.routine_control(0x0203, "start", b"\xAA")     # run routine (0x31)
            assert routine.positive and routine.service == 0x31

            assert uds.write_did(0x2A10, b"\x12\x34").positive          # write (0x2E)
            readback = uds.read_did(0x2A10)                             # read it back (0x22)
            assert readback.positive and readback.data[2:] == b"\x12\x34"

            def invert(seed: bytes) -> bytes:
                return bytes((b ^ 0xFF) & 0xFF for b in seed)

            assert uds.security_access(1, key_fn=invert).positive       # unlock (0x27)
            wrong = uds.security_access(1)                              # echo seed -> invalidKey
            assert not wrong.positive and wrong.nrc == 0x35
    finally:
        server.stop()
