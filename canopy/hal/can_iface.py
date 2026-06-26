"""CAN interface — the one HAL driver shipped in Phase 0.

Thin, backend-agnostic wrapper over :mod:`python-can`. Tests and the test runner talk
to this class, never to ``can.Bus`` directly, so swapping a CANable for a Kvaser (or
``vcan0`` for ``can0``) is a :class:`~canopy.config.CanConfig` change. See CLAUDE.md §5.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from types import TracebackType

import can

from canopy.config import CanConfig


class CanInterface:
    """An open CAN channel.

    Use as a context manager so the underlying bus is always shut down::

        with CanInterface(CanConfig(channel="vcan0")) as iface:
            iface.send(0x123, b"\\x01\\x02")
            for msg in iface.monitor(timeout=2.0):
                print(msg)
    """

    def __init__(self, config: CanConfig | None = None, *, bus: can.BusABC | None = None):
        """Open the channel.

        Args:
            config: Connection settings. Defaults to :meth:`CanConfig.from_env`.
            bus: Pre-constructed bus to adopt instead of opening one. Primarily for
                tests that inject a ``can.interface.Bus(interface="virtual")``.
        """
        self.config = config or CanConfig.from_env()
        self._owns_bus = bus is None
        self._bus = bus or self._open_bus(self.config)

    @staticmethod
    def _open_bus(config: CanConfig) -> can.BusABC:
        kwargs: dict[str, object] = {
            "interface": config.interface,
            "channel": config.channel,
            "receive_own_messages": config.receive_own_messages,
        }
        if config.fd:
            kwargs["fd"] = True
            # SocketCAN reads bitrates from `ip link`; other backends accept them here.
            kwargs["data_bitrate"] = config.data_bitrate
        if config.interface != "socketcan":
            # SocketCAN rejects an explicit bitrate; pass it only to backends that want it.
            kwargs["bitrate"] = config.bitrate
        return can.interface.Bus(**kwargs)

    @property
    def bus(self) -> can.BusABC:
        """The wrapped :class:`can.BusABC`, for advanced/escape-hatch use."""
        return self._bus

    def send(
        self,
        arbitration_id: int,
        data: bytes,
        *,
        is_extended_id: bool = False,
        is_fd: bool | None = None,
        timeout: float | None = 1.0,
    ) -> can.Message:
        """Transmit a single frame and return the sent :class:`can.Message`.

        Args:
            arbitration_id: 11-bit (standard) or 29-bit (extended) CAN ID.
            data: Payload bytes (≤8 for classic CAN, ≤64 for CAN FD).
            is_extended_id: Use a 29-bit identifier.
            is_fd: Force/forbid an FD frame; defaults to the channel's FD setting.
            timeout: Seconds to wait for the frame to enter the TX buffer.
        """
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
            is_fd=self.config.fd if is_fd is None else is_fd,
        )
        self._bus.send(msg, timeout=timeout)
        return msg

    def receive(self, timeout: float | None = 1.0) -> can.Message | None:
        """Block for the next frame, returning ``None`` if ``timeout`` elapses."""
        return self._bus.recv(timeout=timeout)

    def monitor(
        self, *, timeout: float | None = 1.0, limit: int | None = None
    ) -> Iterator[can.Message]:
        """Yield received frames until idle for ``timeout`` or ``limit`` frames seen.

        Args:
            timeout: Idle timeout in seconds; ``None`` blocks forever between frames.
            limit: Stop after this many frames. ``None`` means unbounded.
        """
        count = 0
        while limit is None or count < limit:
            msg = self._bus.recv(timeout=timeout)
            if msg is None:
                return
            yield msg
            count += 1

    def shutdown(self) -> None:
        """Release the channel if this interface opened it."""
        if self._owns_bus and self._bus is not None:
            with contextlib.suppress(Exception):
                self._bus.shutdown()

    def __enter__(self) -> CanInterface:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.shutdown()
