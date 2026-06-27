"""A virtual ECU: periodic broadcaster (+ optional diagnostic responder).

An ECU owns a set of periodic messages it transmits at fixed cycle times, each optionally
E2E-protected with its own rolling alive-counter. The diagnostic (UDS) personality lives
in :mod:`canopy.sim.uds_server` and is attached by the vehicle when configured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from canopy.sim.e2e import E2EProfile

if TYPE_CHECKING:
    from cantools.database.can import Message


@dataclass(slots=True)
class PeriodicMessage:
    """One periodically transmitted frame.

    Attributes:
        message: cantools message definition (carries id, layout, signals).
        signals: Base signal values to transmit (counter/checksum filled in per cycle).
        period_s: Cycle time in seconds.
        e2e: E2E protection profile; default = no counter/checksum.
        is_extended_id: 29-bit identifier.
    """

    message: Message
    signals: dict[str, object]
    period_s: float
    e2e: E2EProfile = field(default_factory=E2EProfile)
    is_extended_id: bool = False
    _counter: int = field(default=0, init=False, repr=False)
    _next_due: float = field(default=0.0, init=False, repr=False)

    @property
    def arbitration_id(self) -> int:
        return self.message.frame_id

    def encode_next(self) -> bytes:
        """Encode this frame for transmission and advance the alive-counter."""
        data = self.e2e.encode(self.message, self.signals, self._counter)
        self._counter = (self._counter + 1) % (self.e2e.counter_max + 1)
        return data


@dataclass
class VirtualEcu:
    """A simulated module.

    Attributes:
        name: Human-readable node name (e.g. "PCM", "BCM").
        messages: Periodic frames this ECU broadcasts.
        request_id / response_id: UDS addressing (if this ECU answers diagnostics).
    """

    name: str
    messages: list[PeriodicMessage] = field(default_factory=list)
    request_id: int | None = None
    response_id: int | None = None
    # UdsServerConfig (kept loosely typed to avoid importing the isotp/udsoncan stack here).
    uds_config: object | None = None

    def add_periodic(
        self,
        message: Message,
        signals: dict[str, object],
        period_s: float,
        e2e: E2EProfile | None = None,
        *,
        is_extended_id: bool = False,
    ) -> PeriodicMessage:
        pm = PeriodicMessage(
            message=message,
            signals=signals,
            period_s=period_s,
            e2e=e2e or E2EProfile(),
            is_extended_id=is_extended_id,
        )
        self.messages.append(pm)
        return pm
