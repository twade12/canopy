"""Command layer — the bytes that *control* a module over CAN.

Three channels turn an intent ("A/C clutch ON") into frames on the wire:

* **raw**   — a CAN id + payload (optionally cyclic).
* **dbc**   — set named signals on a normal application message; ``cantools`` encodes it.
* **uds**   — actuation services over ISO-TP: SecurityAccess (0x27), InputOutputControl
              (0x2F), RoutineControl (0x31), Write/ReadDataByIdentifier (0x2E / 0x22).

This module only *builds request bytes* and *parses responses* (positive vs. negative +
the NRC name) — it owns no transport, so it is trivially testable and reusable by the CLI,
the bench API, and the test runner. A small :class:`CyclicTx` manages periodic frames.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# UDS service ids (ISO 14229)
SID = {
    "session": 0x10, "clear_dtc": 0x14, "read_dtc": 0x19, "read_did": 0x22,
    "security": 0x27, "write_did": 0x2E, "io_control": 0x2F, "routine": 0x31,
    "tester_present": 0x3E,
}

# InputOutputControlParameter (0x2F, byte after the DID)
IO_CONTROL = {
    "return_control": 0x00, "reset_to_default": 0x01, "freeze": 0x02, "short_term_adjust": 0x03,
}
# RoutineControlType (0x31, sub-function)
ROUTINE_CONTROL = {"start": 0x01, "stop": 0x02, "results": 0x03}

# Negative Response Codes — the "why it said no" you'll see constantly while reverse-engineering
NRC = {
    0x10: "generalReject", 0x11: "serviceNotSupported", 0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat", 0x14: "responseTooLong",
    0x22: "conditionsNotCorrect", 0x24: "requestSequenceError", 0x31: "requestOutOfRange",
    0x33: "securityAccessDenied", 0x35: "invalidKey", 0x36: "exceedNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired", 0x70: "uploadDownloadNotAccepted",
    0x78: "responsePending", 0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
}


def _u16(v: int) -> list[int]:
    return [(v >> 8) & 0xFF, v & 0xFF]


def _coerce(control: str | int, table: dict[str, int], default: int) -> int:
    if isinstance(control, int):
        return control
    return table.get(control, default)


# --- UDS request builders -----------------------------------------------------
def build_session(session: int = 1) -> bytes:
    return bytes([0x10, session & 0xFF])


def build_read_did(did: int) -> bytes:
    return bytes([0x22, *_u16(did)])


def build_write_did(did: int, data: bytes = b"") -> bytes:
    return bytes([0x2E, *_u16(did), *data])


def build_io_control(did: int, control: str | int = "short_term_adjust",
                     data: bytes = b"") -> bytes:
    cp = _coerce(control, IO_CONTROL, 0x03)
    return bytes([0x2F, *_u16(did), cp, *data])


def build_routine(routine_id: int, control: str | int = "start", data: bytes = b"") -> bytes:
    ct = _coerce(control, ROUTINE_CONTROL, 0x01)
    return bytes([0x31, ct, *_u16(routine_id), *data])


def build_security_request_seed(level: int = 1) -> bytes:
    return bytes([0x27, level & 0xFF])  # odd sub-function = requestSeed


def build_security_send_key(level: int = 1, key: bytes = b"") -> bytes:
    return bytes([0x27, (level + 1) & 0xFF, *key])  # even sub-function = sendKey


# --- response parsing ---------------------------------------------------------
@dataclass
class UdsResult:
    request: bytes
    response: bytes
    positive: bool
    service: int            # the service id the response refers to
    data: bytes            # payload after the service byte (echoed sub-bytes + data)
    nrc: int | None = None
    nrc_name: str = ""

    @property
    def hex(self) -> str:
        return self.response.hex(" ")

    def __str__(self) -> str:
        if not self.response:
            return "no response (timeout)"
        if self.positive:
            return f"positive 0x{self.service + 0x40:02X} [{self.data.hex(' ')}]"
        if self.nrc is not None:
            return f"negative: {self.nrc_name} (0x{self.nrc:02X})"
        return "negative"


def parse_uds_response(request: bytes, resp: bytes | None) -> UdsResult:
    req_sid = request[0] if request else 0
    if not resp:
        return UdsResult(request, b"", False, req_sid, b"", None, "no response / timeout")
    if resp[0] == 0x7F:  # negative response: 0x7F <service> <nrc>
        nrc = resp[2] if len(resp) > 2 else 0
        sid = resp[1] if len(resp) > 1 else req_sid
        return UdsResult(request, resp, False, sid, b"", nrc, NRC.get(nrc, f"0x{nrc:02X}"))
    return UdsResult(request, resp, True, resp[0] - 0x40, resp[1:], None, "")


# --- DBC signal encode --------------------------------------------------------
def encode_signal_frame(db, message: str | int, signals: dict) -> tuple[int, bytes, bool, bool]:
    """Encode named signals onto an application message -> (arbitration_id, data, ext, fd)."""
    msg = (db.get_message_by_name(message) if isinstance(message, str)
           else db.get_message_by_frame_id(message))
    data = msg.encode(signals, strict=False)
    return (msg.frame_id, bytes(data), bool(msg.is_extended_frame),
            bool(getattr(msg, "is_fd", False)))


# --- cyclic transmit ----------------------------------------------------------
@dataclass
class CyclicTx:
    """Manage periodic frames via the backend's hardware/SW cyclic sender (restbus-style)."""

    bus: object
    _tasks: dict = field(default_factory=dict)

    def start(self, key: str, arbitration_id: int, data: bytes, period_s: float,
              *, is_extended: bool = False, is_fd: bool = False) -> str:
        import can
        self.stop(key)
        msg = can.Message(arbitration_id=arbitration_id, data=data,
                          is_extended_id=is_extended, is_fd=is_fd)
        self._tasks[key] = self.bus.send_periodic(msg, period_s)
        return key

    def stop(self, key: str) -> None:
        task = self._tasks.pop(key, None)
        if task is not None:
            task.stop()

    def stop_all(self) -> None:
        for key in list(self._tasks):
            self.stop(key)

    def active(self) -> list[str]:
        return list(self._tasks)
