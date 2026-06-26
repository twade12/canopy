"""CLI smoke tests that need no bus (decode path) plus arg parsing."""

from __future__ import annotations

from pathlib import Path

import can
from typer.testing import CliRunner

from canopy.cli import _parse_id, app
from canopy.trace import BlfTraceLogger

runner = CliRunner()
DBC = Path(__file__).parent / "data" / "test.dbc"


def test_parse_id_accepts_hex_forms() -> None:
    assert _parse_id("123") == 0x123
    assert _parse_id("0x123") == 0x123
    assert _parse_id("0X7FF") == 0x7FF


def test_decode_command(tmp_path: Path) -> None:
    trace_path = tmp_path / "run.blf"
    with BlfTraceLogger(trace_path) as trace:
        trace.log(can.Message(arbitration_id=0x123, data=b"\xa0\x0f\x3c\x00\x00\x00\x00\x00"))

    result = runner.invoke(app, ["decode", str(trace_path), "--dbc", str(DBC)])
    assert result.exit_code == 0, result.output
    assert "EngineData" in result.output
    assert "EngineSpeed=1000" in result.output
    assert "1 frame(s)" in result.output
