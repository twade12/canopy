"""OBD-II (SAE J1979) Mode 01 — the *standardized*, decipherable layer.

Unlike OEM UDS actuation, OBD-II live data is public and universal: send ``01 <pid>`` and
decode the response ``41 <pid> <bytes>`` with a documented formula. This is the zero-RE
"scan-tool live data" starting point on any module that speaks OBD. Pure functions only —
the transport (ISO-TP over CAN) lives in the bench.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Pid:
    pid: int
    name: str
    unit: str
    nbytes: int
    decode: Callable[[bytes], float]

    @property
    def hex(self) -> str:
        return f"01{self.pid:02X}"


def _a(d: bytes) -> int:
    return d[0]


def _ab(d: bytes) -> int:
    return d[0] * 256 + d[1]


# A curated, high-value subset of Mode 01 PIDs (formulas straight from SAE J1979).
PIDS: dict[int, Pid] = {
    0x04: Pid(0x04, "Engine load", "%", 1, lambda d: _a(d) * 100 / 255),
    0x05: Pid(0x05, "Coolant temp", "°C", 1, lambda d: _a(d) - 40),
    0x06: Pid(0x06, "Short fuel trim B1", "%", 1, lambda d: (_a(d) - 128) * 100 / 128),
    0x07: Pid(0x07, "Long fuel trim B1", "%", 1, lambda d: (_a(d) - 128) * 100 / 128),
    0x0A: Pid(0x0A, "Fuel pressure", "kPa", 1, lambda d: _a(d) * 3),
    0x0B: Pid(0x0B, "Intake MAP", "kPa", 1, _a),
    0x0C: Pid(0x0C, "Engine RPM", "rpm", 2, lambda d: _ab(d) / 4),
    0x0D: Pid(0x0D, "Vehicle speed", "km/h", 1, _a),
    0x0E: Pid(0x0E, "Timing advance", "°", 1, lambda d: _a(d) / 2 - 64),
    0x0F: Pid(0x0F, "Intake air temp", "°C", 1, lambda d: _a(d) - 40),
    0x10: Pid(0x10, "MAF rate", "g/s", 2, lambda d: _ab(d) / 100),
    0x11: Pid(0x11, "Throttle position", "%", 1, lambda d: _a(d) * 100 / 255),
    0x1F: Pid(0x1F, "Run time", "s", 2, _ab),
    0x21: Pid(0x21, "Distance w/ MIL on", "km", 2, _ab),
    0x2F: Pid(0x2F, "Fuel level", "%", 1, lambda d: _a(d) * 100 / 255),
    0x33: Pid(0x33, "Barometric pressure", "kPa", 1, _a),
    0x42: Pid(0x42, "Module voltage", "V", 2, lambda d: _ab(d) / 1000),
    0x46: Pid(0x46, "Ambient air temp", "°C", 1, lambda d: _a(d) - 40),
    0x5C: Pid(0x5C, "Engine oil temp", "°C", 1, lambda d: _a(d) - 40),
    0x5E: Pid(0x5E, "Fuel rate", "L/h", 2, lambda d: _ab(d) / 20),
}


def build_request(pid: int) -> bytes:
    """ISO-TP payload for a Mode 01 request (the bench adds the transport framing)."""
    return bytes([0x01, pid])


def parse_response(pid: int, resp: bytes | None) -> float | None:
    """Decode a ``41 <pid> <data…>`` response to an engineering value, or None."""
    spec = PIDS.get(pid)
    if not spec or not resp or len(resp) < 2 or resp[0] != 0x41 or resp[1] != pid:
        return None
    data = resp[2:2 + spec.nbytes]
    if len(data) < spec.nbytes:
        return None
    try:
        return round(float(spec.decode(data)), 2)
    except (ValueError, IndexError, ZeroDivisionError):
        return None


def catalog() -> list[dict]:
    """The PID catalog as plain dicts (for the UI's live-data picker)."""
    return [{"pid": p.pid, "hex": f"0x{p.pid:02X}", "name": p.name, "unit": p.unit}
            for p in PIDS.values()]
