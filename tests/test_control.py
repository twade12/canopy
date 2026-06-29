"""OBD-II PIDs, seed/key registry, capture/learn, and the sequence runner."""

from __future__ import annotations

from canopy import obd
from canopy.hal import capture, seedkey
from canopy.runner import run_sequence
from canopy.runner.sequence import report_markdown


# --- OBD-II -------------------------------------------------------------------
def test_obd_request_and_decode() -> None:
    assert obd.build_request(0x0C) == bytes([0x01, 0x0C])
    # RPM: (256*A + B)/4 -> 0x0B,0xB8 = 3000 rpm
    assert obd.parse_response(0x0C, bytes([0x41, 0x0C, 0x0B, 0xB8])) == 750.0
    # Coolant temp A-40 -> 0x5A = 50 C
    assert obd.parse_response(0x05, bytes([0x41, 0x05, 0x5A])) == 50.0
    assert obd.parse_response(0x0C, bytes([0x41, 0x0D, 0x00])) is None   # wrong pid echo
    assert obd.parse_response(0x0C, b"") is None
    assert any(p["name"] == "Engine RPM" for p in obd.catalog())


# --- seed/key -----------------------------------------------------------------
def test_seedkey_registry() -> None:
    assert "xor_ff" in seedkey.names()
    fn = seedkey.get("xor_ff")
    assert fn(bytes([0x11, 0x22])) == bytes([0xEE, 0xDD])
    assert seedkey.get("nope") is None
    seedkey.register("plus2", lambda s: bytes((b + 2) & 0xFF for b in s))
    assert seedkey.get("plus2")(b"\x01") == b"\x03"


# --- capture / learn ----------------------------------------------------------
def test_reassemble_single_and_multiframe() -> None:
    assert capture.reassemble_isotp([bytes([0x02, 0x2F, 0x4A])]) == bytes([0x2F, 0x4A])
    multi = [bytes([0x10, 0x0A, 0x62, 0xF1, 0x90, 0x31, 0x46, 0x54]),
             bytes([0x21, 0x37, 0x57, 0x32, 0x42])]
    assert capture.reassemble_isotp(multi) == \
        bytes([0x62, 0xF1, 0x90, 0x31, 0x46, 0x54, 0x37, 0x57, 0x32, 0x42])


def test_parse_uds_request_kinds() -> None:
    assert capture.parse_uds_request(bytes([0x2F, 0x4A, 0x01, 0x03, 0x01])) == {
        "kind": "uds_io", "did": "0x4A01", "control": "short_term_adjust", "value_hex": "01"}
    assert capture.parse_uds_request(bytes([0x31, 0x01, 0x02, 0x03]))["kind"] == "uds_routine"
    assert capture.parse_uds_request(bytes([0x2E, 0x2A, 0x10, 0x12]))["did"] == "0x2A10"


def test_propose_command_from_capture() -> None:
    frames = [
        (0x7E0, bytes([0x05, 0x2F, 0x4A, 0x01, 0x03, 0x01])),   # tester request (single frame)
        (0x7E8, bytes([0x05, 0x6F, 0x4A, 0x01, 0x03, 0x01])),   # ECU positive response
    ]
    out = capture.propose_command(frames, 0x7E0, 0x7E8)
    assert out["command"]["kind"] == "uds_io" and out["command"]["did"] == "0x4A01"
    assert out["positive"] is True


# --- runner -------------------------------------------------------------------
def test_run_sequence_with_measurement() -> None:
    def execute(spec):
        return {"positive": True, "summary": spec.get("name", ""), "response_hex": "6F 4A 01"}

    def measure(_quantity):
        return 6.0  # amps

    steps = [
        {"name": "A/C clutch ON", "command": {"name": "A/C clutch ON"},
         "expect": {"positive": True, "measure": {"quantity": "current_a", "min": 4, "max": 8}}},
        {"name": "Bad expectation", "command": {"name": "x"}, "expect": {"positive": False}},
    ]
    results = run_sequence(steps, execute, measure)
    assert results[0].ok and results[0].measured == 6.0
    assert results[1].ok is False                       # expected negative, got positive
    md = report_markdown(results)
    assert "1/2 steps passed" in md
