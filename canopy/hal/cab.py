"""Host-side client for the CAB backplane (see docs/CAB-PROTOCOL.md).

`CABLink` speaks newline-delimited JSON over USB-CDC serial to the backplane management MCU.
`MockCABLink` simulates a populated bench so the test runner and UI can be built and tested with
NO hardware. `make_cab_link()` returns the real link if a serial port is given (and pyserial is
installed), else the mock.

Safety contract is enforced client-side too: outputs start safe/open and require an explicit
`arm()` after configuration; `estop()`/`reset()` return everything to safe.
"""

from __future__ import annotations

import json
import time

PROTOCOL_VERSION = "1.0"

# Cards the bench can report (CAB 10-slot reference).
KNOWN_CARDS = [
    "CAB-PWR-IGN", "CAB-NET-4CAN-4LIN", "CAB-SENS-8V-8R", "CAB-PATTERN-12CH",
    "CAB-DIG-32SW", "CAB-LOAD-16", "CAB-SAFE-SQUIB-8", "CAB-MOTOR-HB-8",
    "CAB-IPC-DISPLAY", "CAB-LIGHT-HCM-ALCM",
]


class CABError(RuntimeError):
    """Raised on a CAB protocol/transport error."""


class CABLink:
    """Base interface. Subclasses implement `_txn` (one request → one response dict)."""

    def __init__(self) -> None:
        self._id = 0

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _txn(self, msg: dict) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError

    def _command(self, op: str, **fields) -> dict:
        msg = {"id": self._next_id(), "op": op, **fields}
        resp = self._txn(msg)
        if not resp.get("ok", False):
            raise CABError(resp.get("error", f"CAB {op} failed"))
        return resp

    # --- protocol surface (docs/CAB-PROTOCOL.md) ---
    def hello(self) -> dict:
        return self._command("hello")

    def status(self) -> dict:
        return self._command("status")

    def health(self) -> dict:
        return self._command("health")

    def reset(self) -> dict:
        return self._command("reset")

    def set_channel(self, card: str, channel: str, mode: str,
                    value: dict | None = None, fault_injection: str = "none") -> dict:
        return self._command("set", card=card, channel=channel, mode=mode,
                             value=value or {}, fault_injection=fault_injection)

    def read(self, card: str, channel: str) -> dict:
        return self._command("read", card=card, channel=channel)

    def arm(self, card: str = "ALL") -> dict:
        return self._command("arm", card=card)

    def disarm(self, card: str = "ALL") -> dict:
        return self._command("disarm", card=card)

    def estop(self) -> dict:
        return self._command("estop")

    def close(self) -> None:
        pass


class MockCABLink(CABLink):
    """Simulated bench: a fully populated 10-slot CAB, safe-by-default, that gives plausible
    readbacks so the rest of the stack can be developed without hardware."""

    def __init__(self, cards: list[str] | None = None) -> None:
        super().__init__()
        self.cards = cards or list(KNOWN_CARDS)
        self.armed: set[str] = set()
        self.config: dict[tuple[str, str], dict] = {}

    def _txn(self, msg: dict) -> dict:
        op = msg.get("op")
        rid = msg.get("id")
        if op == "hello":
            return {"id": rid, "ok": True, "fw": "mock-1.0.0",
                    "protocol": PROTOCOL_VERSION, "cards": self.cards}
        if op == "status":
            return {"id": rid, "ok": True, "estop": False, "armed": sorted(self.armed),
                    "rails": {"vbat": 13.5 if self.armed else 0.0, "5v": 5.0, "3v3": 3.3},
                    "temp_c": 30, "cards": self.cards}
        if op == "health":
            return {"id": rid, "ok": True, "health": [
                {"card": c, "fw": "mock-1.0.0", "temp_c": 30, "faults": [],
                 "armed": c in self.armed} for c in self.cards]}
        if op == "reset":
            self.armed.clear()
            self.config.clear()
            return {"id": rid, "ok": True}
        if op == "estop":
            self.armed.clear()
            return {"id": rid, "ok": True, "estop": True}
        card = msg.get("card", "")
        if op in ("set", "read", "arm", "disarm") and card != "ALL" and card not in self.cards:
            return {"id": rid, "ok": False, "error": f"card {card} not present"}
        if op == "set":
            self.config[(card, msg.get("channel", ""))] = msg.get("value", {})
            return {"id": rid, "ok": True, "readback": msg.get("value", {})}
        if op == "read":
            # plausible quiescent measurement for dev
            val = {"current_a": 0.045, "voltage_v": 13.5} if card == "CAB-PWR-IGN" \
                else {"value": 0.0}
            return {"id": rid, "ok": True, "readback": val, "ts": int(time.time() * 1000)}
        if op == "arm":
            self.armed.update(self.cards if card == "ALL" else [card])
            return {"id": rid, "ok": True, "armed": sorted(self.armed)}
        if op == "disarm":
            self.armed.difference_update(self.cards if card == "ALL" else [card])
            return {"id": rid, "ok": True, "armed": sorted(self.armed)}
        return {"id": rid, "ok": False, "error": f"unknown op {op}"}


class SerialCABLink(CABLink):
    """Real link over USB-CDC serial (pyserial). Synchronous request/response; async events
    (no `id`) are collected in `self.events`."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0) -> None:
        super().__init__()
        import serial  # lazy: only needed with hardware
        self._ser = serial.Serial(port, baudrate, timeout=timeout)
        self.events: list[dict] = []

    def _txn(self, msg: dict) -> dict:
        self._ser.write((json.dumps(msg) + "\n").encode("utf-8"))
        deadline = time.time() + 3.0
        while time.time() < deadline:
            line = self._ser.readline().decode("utf-8").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "event" in obj:
                self.events.append(obj)
                continue
            if obj.get("id") == msg["id"]:
                return obj
        raise CABError("CAB serial timeout")

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass


def make_cab_link(port: str | None = None) -> CABLink:
    """Real link if a serial port is given and pyserial is available; otherwise the mock bench."""
    if port:
        try:
            return SerialCABLink(port)
        except Exception:
            pass
    return MockCABLink()
