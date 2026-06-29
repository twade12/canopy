"""USB-to-CAN bench: connect to a CAN interface, probe an ECU, send/observe frames.

A thin bridge from the vision server to the existing CAN/UDS stack
(:mod:`canopy.hal`). It lets the UI connect to a local USB-to-CAN adapter (any SocketCAN
device, or a ``virtual``/``vcan0`` bus), confirm ECU connectivity, send raw frames, run UDS
requests (incl. actuator/output controls), and watch live traffic.

This is the seed of the "car-in-a-box" bench control. It is intentionally simple and
single-connection; the full station HAL (matrix, power, multi-bus) plugs in later.
"""

from __future__ import annotations

import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from canopy import obd
from canopy.config import CanConfig
from canopy.hal import capture, seedkey
from canopy.hal import commands as cmdmod
from canopy.hal.can_iface import CanInterface
from canopy.hal.isotp import make_can_stack
from canopy.vision.restbus import RestbusSimulator


def _parse_hex(v, default: int = 0) -> int:
    if v is None or v == "":
        return default
    if isinstance(v, int):
        return v
    return int(str(v), 16) if str(v).lower().startswith("0x") else int(str(v), 16)


def _hexbytes(s) -> bytes:
    s = (s or "").replace("0x", "").replace(" ", "")
    return bytes.fromhex(s) if s else b""


def dtc_to_str(b0: int, b1: int, b2: int) -> str:
    """3-byte UDS DTC -> standard string, e.g. P0420 (+ b2 = failure-type byte)."""
    sysname = ["P", "C", "B", "U"][(b0 >> 6) & 0x3]
    return f"{sysname}{(b0 >> 4) & 0x3}{b0 & 0xF:X}{b1 >> 4:X}{b1 & 0xF:X}"


def list_can_interfaces() -> list[dict]:
    """Best-effort discovery of usable CAN channels."""
    found: list[dict] = []
    try:
        out = subprocess.run(
            ["ip", "-br", "link", "show", "type", "can"], capture_output=True, text=True, timeout=3
        )
        for line in out.stdout.splitlines():
            parts = line.split()
            if parts:
                found.append({"interface": "socketcan", "channel": parts[0],
                              "state": parts[1] if len(parts) > 1 else "?"})
    except Exception:
        pass
    # vcan (virtual CAN) devices too
    try:
        out = subprocess.run(
            ["ip", "-br", "link", "show", "type", "vcan"], capture_output=True, text=True, timeout=3
        )
        for line in out.stdout.splitlines():
            parts = line.split()
            if parts and not any(f["channel"] == parts[0] for f in found):
                found.append({"interface": "socketcan", "channel": parts[0], "state": "UP"})
    except Exception:
        pass
    # in-process virtual backend is always available for dry-runs
    found.append({"interface": "virtual", "channel": "canopy-bench", "state": "VIRTUAL"})
    return found


@dataclass
class BenchManager:
    """Holds the single active bench CAN connection and a rolling frame buffer."""

    iface: CanInterface | None = None
    config: CanConfig | None = None
    frames: deque = field(default_factory=lambda: deque(maxlen=600))
    _seq: int = 0
    _thread: threading.Thread | None = None
    _stop: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    restbus: RestbusSimulator = field(default_factory=RestbusSimulator)

    # --- connection ------------------------------------------------------------
    def status(self) -> dict:
        return {
            "connected": self.iface is not None,
            "interface": self.config.interface if self.config else None,
            "channel": self.config.channel if self.config else None,
            "bitrate": self.config.bitrate if self.config else None,
            "frames": self._seq,
        }

    def connect(
        self, interface: str, channel: str, bitrate: int = 500000, fd: bool = False
    ) -> dict:
        self.disconnect()
        self.config = CanConfig(interface=interface, channel=channel, bitrate=bitrate, fd=fd)
        self.iface = CanInterface(self.config)
        self.frames.clear()
        self._seq = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        return self.status()

    def _monitor(self) -> None:
        assert self.iface is not None
        while not self._stop.is_set():
            try:
                msg = self.iface.receive(timeout=0.3)
            except Exception:
                break
            if msg is None:
                continue
            with self._lock:
                self._seq += 1
                self.frames.append({
                    "seq": self._seq,
                    "t": round(time.time(), 3),
                    "id": f"{msg.arbitration_id:X}",
                    "ext": bool(msg.is_extended_id),
                    "data": bytes(msg.data).hex(" "),
                })

    def disconnect(self) -> dict:
        self.restbus.stop()
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        if self.iface is not None:
            self.iface.shutdown()
            self.iface = None
        return {"connected": False}

    def recent_frames(self, since: int = 0) -> list[dict]:
        with self._lock:
            out = [dict(f) for f in self.frames if f["seq"] > since]
        if self.restbus.db is not None:
            for f in out:
                raw = bytes.fromhex(f["data"].replace(" ", ""))
                dec = self.restbus.decode(int(f["id"], 16), raw)
                if dec:
                    f["decoded"] = dec
        return out

    # --- restbus (broadcast the absent ECUs so the DUT wakes up) ---------------
    def restbus_start(self, names: list[str] | None = None) -> dict:
        if self.iface is None:
            raise RuntimeError("not connected")
        return self.restbus.start(self.iface.bus, names)

    def restbus_stop(self) -> dict:
        return self.restbus.stop()

    def read_dtcs(self, request_id: int, response_id: int) -> dict:
        """UDS ReadDTCInformation (0x19 0x02) -> decoded DTC list."""
        r = self.uds_request(request_id, response_id, b"\x19\x02\xff", timeout=2.5)
        if not r.get("ok") or not r.get("response"):
            return {"ok": False, "error": r.get("error", "no response"), "dtcs": []}
        raw = bytes.fromhex(r["response"].replace(" ", ""))
        if len(raw) < 3 or raw[0] != 0x59:
            return {"ok": False, "error": "unexpected response", "dtcs": []}
        body = raw[3:]
        dtcs = []
        for i in range(0, len(body) - 3, 4):
            b0, b1, b2, status = body[i], body[i + 1], body[i + 2], body[i + 3]
            dtcs.append({"code": dtc_to_str(b0, b1, b2), "ftb": f"0x{b2:02X}",
                         "status": f"0x{status:02X}", "confirmed": bool(status & 0x08)})
        return {"ok": True, "dtcs": dtcs}

    # --- sending ---------------------------------------------------------------
    def send_frame(self, arbitration_id: int, data: bytes, *, extended: bool = False) -> dict:
        if self.iface is None:
            raise RuntimeError("not connected")
        msg = self.iface.send(arbitration_id, data, is_extended_id=extended)
        return {"sent": True, "id": f"{msg.arbitration_id:X}", "data": bytes(msg.data).hex(" ")}

    # --- UDS -------------------------------------------------------------------
    def uds_request(self, request_id: int, response_id: int, payload: bytes,
                    *, timeout: float = 2.0) -> dict:
        """Send a raw UDS request over ISO-TP and return the response bytes (or a timeout)."""
        if self.config is None:
            raise RuntimeError("not connected")
        cfg = CanConfig(interface=self.config.interface, channel=self.config.channel,
                        bitrate=self.config.bitrate, fd=self.config.fd, receive_own_messages=False)
        iface = CanInterface(cfg)
        stack = make_can_stack(iface.bus, request_id, response_id)
        try:
            stack.start()
            stack.send(bytes(payload))
            resp = stack.recv(block=True, timeout=timeout)
        finally:
            stack.stop()
            iface.shutdown()
        if not resp:
            return {"ok": False, "error": "no response (timeout)"}
        resp = bytes(resp)
        negative = len(resp) >= 3 and resp[0] == 0x7F
        return {
            "ok": not negative,
            "response": resp.hex(" "),
            "sid": f"0x{resp[0]:02X}",
            "nrc": f"0x{resp[2]:02X}" if negative else None,
        }

    def ping_ecu(self, request_id: int, response_id: int) -> dict:
        """Confirm connectivity: tester-present, then read VIN (DID F190) and DTC count."""
        results: dict = {"request_id": f"0x{request_id:X}", "response_id": f"0x{response_id:X}"}
        tp = self.uds_request(request_id, response_id, b"\x3e\x00", timeout=1.5)
        results["tester_present"] = tp.get("ok", False)
        results["connected"] = tp.get("ok", False)
        vin = self.uds_request(request_id, response_id, b"\x22\xf1\x90", timeout=2.0)
        if vin.get("ok") and vin.get("response"):
            raw = bytes.fromhex(vin["response"].replace(" ", ""))
            if len(raw) > 3 and raw[0] == 0x62:
                results["vin"] = raw[3:].decode("ascii", "ignore").strip("\x00 ")
        dtc = self.uds_request(request_id, response_id, b"\x19\x02\xff", timeout=2.0)
        if dtc.get("ok") and dtc.get("response"):
            raw = bytes.fromhex(dtc["response"].replace(" ", ""))
            if len(raw) >= 3 and raw[0] == 0x59:
                results["dtc_count"] = max(0, (len(raw) - 3) // 4)
        return results

    # --- OBD-II live data (standardized, zero reverse-engineering) -------------
    def obd_read(self, pids: list[int], request_id: int = 0x7E0,
                 response_id: int = 0x7E8) -> list[dict]:
        out = []
        for pid in pids:
            spec = obd.PIDS.get(pid)
            if not spec:
                continue
            r = self.uds_request(request_id, response_id, obd.build_request(pid), timeout=1.2)
            resp = bytes.fromhex(r["response"].replace(" ", "")) if r.get("response") else b""
            out.append({"pid": f"0x{pid:02X}", "name": spec.name, "unit": spec.unit,
                        "value": obd.parse_response(pid, resp)})
        return out

    # --- learn by observation (capture -> diff -> propose a labeled command) ----
    def capture_mark(self) -> int:
        """Snapshot the frame counter; trigger the function, then call capture_diff()."""
        return self._seq

    def capture_diff(self, since: int, request_id: int, response_id: int) -> dict | None:
        frames = [(int(f["id"], 16), bytes.fromhex(f["data"].replace(" ", "")))
                  for f in self.recent_frames(since)]
        return capture.propose_command(frames, request_id, response_id)

    # --- run a command (raw / dbc / uds actuation), the unified executor -------
    def run_command(self, spec: dict, *, key_algo: str = "") -> dict:
        kind = spec.get("kind", "raw")
        rid = _parse_hex(spec.get("request_id"), 0x7E0)
        rsp = _parse_hex(spec.get("response_id"), 0x7E8)

        if kind == "raw":
            arb = _parse_hex(spec.get("arbitration_id"), 0)
            data = _hexbytes(spec.get("data_hex"))
            self.send_frame(arb, data, extended=bool(spec.get("is_fd")) and arb > 0x7FF)
            return {"positive": True, "summary": f"sent 0x{arb:X} [{data.hex(' ')}]",
                    "response_hex": ""}
        if kind == "dbc":
            if self.restbus.db is None:
                return {"positive": False, "summary": "no DBC loaded", "response_hex": ""}
            arb, data, ext, is_fd = cmdmod.encode_signal_frame(
                self.restbus.db, spec.get("message", ""), spec.get("signals", {}))
            self.send_frame(arb, data, extended=ext)
            return {"positive": True, "summary": f"sent {spec.get('message')} [{data.hex(' ')}]",
                    "response_hex": ""}

        # UDS kinds — enter session / unlock security first if required
        req = spec.get("requires", {}) or {}
        if req.get("session", 1) != 1 or req.get("security_level", 0):
            session = int(req.get("session", 3))
            self.uds_request(rid, rsp, cmdmod.build_session(session), timeout=1.5)
        if req.get("security_level", 0):
            self._unlock(rid, rsp, int(req["security_level"]), key_algo)

        did = _parse_hex(spec.get("did"), 0)
        val = _hexbytes(spec.get("value_hex"))
        if kind == "uds_io":
            payload = cmdmod.build_io_control(did, spec.get("control") or "short_term_adjust", val)
        elif kind == "uds_routine":
            payload = cmdmod.build_routine(did, spec.get("control") or "start", val)
        elif kind == "uds_write":
            payload = cmdmod.build_write_did(did, val)
        elif kind == "uds_read":
            payload = cmdmod.build_read_did(did)
        else:
            return {"positive": False, "summary": f"unknown kind {kind}", "response_hex": ""}

        r = self.uds_request(rid, rsp, payload, timeout=2.5)
        resp = bytes.fromhex(r["response"].replace(" ", "")) if r.get("response") else b""
        res = cmdmod.parse_uds_response(payload, resp)
        return {"positive": res.positive, "service": f"0x{res.service:02X}",
                "summary": str(res), "response_hex": res.hex,
                "nrc_name": res.nrc_name}

    def _unlock(self, rid: int, rsp: int, level: int, key_algo: str) -> dict:
        seed_r = self.uds_request(rid, rsp, cmdmod.build_security_request_seed(level), timeout=1.5)
        raw = bytes.fromhex(seed_r["response"].replace(" ", "")) if seed_r.get("response") else b""
        if len(raw) < 2 or raw[0] != 0x67:
            return {"positive": False, "summary": "seed request failed"}
        seed = raw[2:]
        fn = seedkey.get(key_algo) if key_algo else None
        key = fn(seed) if fn else seed
        key_r = self.uds_request(rid, rsp, cmdmod.build_security_send_key(level, key), timeout=1.5)
        ok = bool(key_r.get("ok"))
        return {"positive": ok, "summary": "unlocked" if ok else "invalid key"}
