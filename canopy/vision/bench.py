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

from canopy.config import CanConfig
from canopy.hal.can_iface import CanInterface
from canopy.hal.isotp import make_can_stack
from canopy.vision.restbus import RestbusSimulator


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
