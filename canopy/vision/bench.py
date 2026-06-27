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
            return [f for f in self.frames if f["seq"] > since]

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
