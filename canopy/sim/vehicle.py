"""The virtual vehicle: schedules every ECU's restbus traffic on a CAN channel.

Drives all periodic frames at their cycle times and (optionally) brings up each ECU's UDS
responder, so a module under test sees a fully populated, awake network. Designed to be
testable without timing: :meth:`tick` sends exactly the frames currently due, so tests can
advance a clock by hand; the background thread just calls :meth:`tick` in a loop.
"""

from __future__ import annotations

import threading
import time
from types import TracebackType

from canopy.hal.can_iface import CanInterface
from canopy.sim.ecu import VirtualEcu


class VirtualVehicle:
    """A set of virtual ECUs broadcasting on one CAN channel.

    Args:
        iface: Open CAN interface used to transmit restbus frames.
        ecus: The virtual modules making up this vehicle.
        name: Platform label (e.g. "ford_f250_6.7").
    """

    def __init__(
        self, iface: CanInterface, ecus: list[VirtualEcu] | None = None, *, name: str = "vehicle"
    ):
        self.iface = iface
        self.ecus: list[VirtualEcu] = ecus or []
        self.name = name
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._uds_servers: list[object] = []
        self.frames_sent = 0

    def add_ecu(self, ecu: VirtualEcu) -> VirtualEcu:
        self.ecus.append(ecu)
        return ecu

    @property
    def periodic_messages(self):
        for ecu in self.ecus:
            yield from ecu.messages

    def reset_schedule(self, now: float) -> None:
        """Arm every periodic message to fire immediately at `now`."""
        for pm in self.periodic_messages:
            pm._next_due = now

    def tick(self, now: float) -> int:
        """Transmit every frame whose cycle time has elapsed by `now`. Returns count sent."""
        sent = 0
        for pm in self.periodic_messages:
            if now >= pm._next_due:
                data = pm.encode_next()
                self.iface.send(pm.arbitration_id, data, is_extended_id=pm.is_extended_id)
                pm._next_due = now + pm.period_s
                sent += 1
        self.frames_sent += sent
        return sent

    # --- background operation --------------------------------------------------
    def start(self, *, resolution_s: float = 0.002) -> None:
        """Begin broadcasting in a background thread and start any UDS responders."""
        if self._thread is not None:
            raise RuntimeError("vehicle already started")
        self._start_uds_servers()
        self._stop.clear()
        self.reset_schedule(time.monotonic())
        self._thread = threading.Thread(target=self._run, args=(resolution_s,), daemon=True)
        self._thread.start()

    def _run(self, resolution_s: float) -> None:
        while not self._stop.is_set():
            self.tick(time.monotonic())
            time.sleep(resolution_s)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        for server in self._uds_servers:
            server.stop()  # type: ignore[attr-defined]
        self._uds_servers.clear()

    def _start_uds_servers(self) -> None:
        # Lazy import: UDS pulls in isotp/udsoncan, not needed for pure restbus.
        from canopy.sim.uds_server import UdsServer

        for ecu in self.ecus:
            cfg = getattr(ecu, "uds_config", None)
            if cfg is None or ecu.request_id is None or ecu.response_id is None:
                continue
            server = UdsServer(
                channel=self.iface.config,
                request_id=ecu.request_id,
                response_id=ecu.response_id,
                config=cfg,
            )
            server.start()
            self._uds_servers.append(server)

    def __enter__(self) -> VirtualVehicle:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.stop()
