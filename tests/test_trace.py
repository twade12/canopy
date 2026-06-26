"""BLF trace logger round-trip."""

from __future__ import annotations

from pathlib import Path

import can

from canopy.trace import BlfTraceLogger, default_trace_path, read_trace


def test_blf_write_then_read(tmp_path: Path) -> None:
    path = tmp_path / "run.blf"
    with BlfTraceLogger(path) as trace:
        trace.log(can.Message(arbitration_id=0x123, data=b"\x01\x02"))
        trace.log(can.Message(arbitration_id=0x456, data=b"\x03\x04\x05"))

    messages = read_trace(path)
    assert [m.arbitration_id for m in messages] == [0x123, 0x456]
    assert bytes(messages[0].data) == b"\x01\x02"


def test_default_trace_path_shape(tmp_path: Path) -> None:
    path = default_trace_path("dtc-scan", directory=tmp_path)
    assert path.parent == tmp_path
    assert path.name.endswith("_dtc-scan.blf")
