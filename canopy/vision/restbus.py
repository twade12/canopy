"""Restbus simulation + DBC decode (cantools over python-can).

Restbus = broadcasting the periodic frames the *absent* ECUs would send (gateway heartbeat,
ignition status, network management, vehicle speed, ...) so a module under test leaves limp/sleep
mode and behaves as if installed in the car. Driven by a platform DBC. Works on a real CANable
(SocketCAN ``can0``) or the ``vcan0`` dev loop identically.

Kept dependency-light: cantools for the DBC, python-can's ``send_periodic`` for transmission.
"""

from __future__ import annotations

import os

import can
import cantools


def _default_data(msg) -> bytes:
    """Encode a message at its signals' initial/minimum/zero values (a safe idle frame)."""
    try:
        values = {}
        for s in msg.signals:
            if s.initial is not None:
                values[s.name] = s.initial
            elif s.minimum is not None:
                values[s.name] = s.minimum
            else:
                values[s.name] = 0
        return bytes(msg.encode(values, strict=False, padding=True))
    except Exception:
        return bytes(msg.length or 8)


class RestbusSimulator:
    def __init__(self) -> None:
        self.db = None
        self.dbc_name: str = ""
        self._tasks: dict[str, object] = {}

    # --- DBC ---
    def load_dbc(self, path: str) -> dict:
        self.db = cantools.database.load_file(path)
        self.dbc_name = os.path.basename(path)
        return self.summary()

    def summary(self) -> dict:
        if self.db is None:
            return {"loaded": False}
        msgs = [{
            "name": m.name, "id": f"{m.frame_id:X}", "cycle_ms": m.cycle_time or 0,
            "signals": [s.name for s in m.signals], "len": m.length,
            "running": m.name in self._tasks,
        } for m in self.db.messages]
        return {"loaded": True, "dbc": self.dbc_name, "messages": msgs,
                "running": list(self._tasks), "count": len(self._tasks)}

    # --- transmit (restbus) ---
    def start(self, bus: can.BusABC, names: list[str] | None = None) -> dict:
        if self.db is None:
            raise RuntimeError("no DBC loaded")
        self.stop()
        for m in self.db.messages:
            ct = m.cycle_time or 0
            if ct <= 0:
                continue
            if names and m.name not in names:
                continue
            msg = can.Message(arbitration_id=m.frame_id, data=_default_data(m),
                              is_extended_id=m.is_extended_frame)
            try:
                self._tasks[m.name] = bus.send_periodic(msg, ct / 1000.0)
            except Exception:
                continue
        return self.summary()

    def stop(self) -> dict:
        for task in self._tasks.values():
            try:
                task.stop()
            except Exception:
                pass
        self._tasks = {}
        return self.summary()

    @property
    def running(self) -> bool:
        return bool(self._tasks)

    # --- decode (live monitor) ---
    def decode(self, frame_id: int, data: bytes) -> dict | None:
        if self.db is None:
            return None
        try:
            m = self.db.get_message_by_frame_id(frame_id)
            decoded = m.decode(bytes(data), decode_choices=True, allow_truncated=True)
            return {"name": m.name,
                    "signals": {k: (str(v) if not isinstance(v, (int, float)) else round(v, 3))
                                for k, v in decoded.items()}}
        except Exception:
            return None
