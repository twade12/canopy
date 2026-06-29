"""Learn-by-observation: turn captured CAN traffic into a labeled Command.

The flow: sniff the bus while a bidirectional scan tool (or the in-car switch) triggers a
function, reassemble the ISO-TP request/response, classify the UDS service, and propose a
:class:`~canopy.profiles.schema.Command`. One click saves it — so every function you watch
becomes a reusable button. Pure functions; the bench owns the live buffer.
"""

from __future__ import annotations

from canopy.hal import commands as cmd

_IO_NAME = {v: k for k, v in cmd.IO_CONTROL.items()}
_RTN_NAME = {v: k for k, v in cmd.ROUTINE_CONTROL.items()}


def reassemble_isotp(frames: list[bytes]) -> bytes | None:
    """Reassemble an ISO-TP (single or multi-frame) message from one id's data fields."""
    if not frames or not frames[0]:
        return None
    f0 = frames[0]
    pci = f0[0] >> 4
    if pci == 0x0:  # SingleFrame: [0x0L, data…]
        length = f0[0] & 0x0F
        return bytes(f0[1:1 + length])
    if pci == 0x1:  # FirstFrame: [0x1L, LL, data…] then ConsecutiveFrames [0x2N, data…]
        length = ((f0[0] & 0x0F) << 8) | f0[1]
        data = bytearray(f0[2:])
        for frame in frames[1:]:
            if frame and (frame[0] >> 4) == 0x2:
                data += frame[1:]
            if len(data) >= length:
                break
        return bytes(data[:length])
    return None  # FlowControl / unknown


def parse_uds_request(payload: bytes) -> dict:
    """Classify a reassembled request into Command fields (kind/did/control/value)."""
    if not payload:
        return {"kind": "raw"}
    sid = payload[0]
    if sid == 0x2F and len(payload) >= 4:
        did = (payload[1] << 8) | payload[2]
        return {"kind": "uds_io", "did": f"0x{did:04X}",
                "control": _IO_NAME.get(payload[3], str(payload[3])),
                "value_hex": payload[4:].hex()}
    if sid == 0x31 and len(payload) >= 4:
        rid = (payload[2] << 8) | payload[3]
        return {"kind": "uds_routine", "did": f"0x{rid:04X}",
                "control": _RTN_NAME.get(payload[1], str(payload[1])),
                "value_hex": payload[4:].hex()}
    if sid == 0x2E and len(payload) >= 3:
        did = (payload[1] << 8) | payload[2]
        return {"kind": "uds_write", "did": f"0x{did:04X}", "value_hex": payload[3:].hex()}
    if sid == 0x22 and len(payload) >= 3:
        did = (payload[1] << 8) | payload[2]
        return {"kind": "uds_read", "did": f"0x{did:04X}"}
    return {"kind": "raw", "data_hex": payload.hex()}


def propose_command(
    frames: list[tuple[int, bytes]], request_id: int, response_id: int) -> dict | None:
    """From captured (arb_id, data) frames, propose a Command for the request/response pair."""
    req = reassemble_isotp([d for (i, d) in frames if i == request_id])
    rsp = reassemble_isotp([d for (i, d) in frames if i == response_id])
    if not req:
        return None
    spec = parse_uds_request(req)
    spec["request_id"] = f"0x{request_id:X}"
    spec["response_id"] = f"0x{response_id:X}"
    res = cmd.parse_uds_response(req, rsp) if rsp else None
    return {
        "command": spec,
        "request_hex": req.hex(" "),
        "response_hex": rsp.hex(" ") if rsp else "",
        "positive": bool(res and res.positive),
        "nrc_name": res.nrc_name if (res and not res.positive) else "",
    }
