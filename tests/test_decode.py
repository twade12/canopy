"""Decode tests against the bundled minimal DBC."""

from __future__ import annotations

from pathlib import Path

import can

from canopy.decode import Decoder

DBC = Path(__file__).parent / "data" / "test.dbc"


def test_decode_known_frame() -> None:
    decoder = Decoder.from_files(DBC)
    # EngineSpeed=1000rpm -> raw 4000 (0x0FA0, LE); CoolantTemp=20degC -> raw 60 (0x3C).
    msg = can.Message(arbitration_id=0x123, data=b"\xa0\x0f\x3c\x00\x00\x00\x00\x00")
    decoded = decoder.decode(msg)

    assert decoded is not None
    assert decoded.name == "EngineData"
    assert decoded.signals["EngineSpeed"] == 1000
    assert decoded.signals["CoolantTemp"] == 20


def test_decode_unknown_frame_returns_none() -> None:
    decoder = Decoder.from_files(DBC)
    msg = can.Message(arbitration_id=0x7FF, data=b"\x00")
    assert decoder.decode(msg) is None


def test_format_falls_back_for_unknown() -> None:
    decoder = Decoder.from_files(DBC)
    msg = can.Message(arbitration_id=0x7FF, data=b"\xde\xad")
    text = decoder.format(msg)
    assert "unknown" in text
    assert "de ad" in text
