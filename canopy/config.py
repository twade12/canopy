"""CAN bus configuration.

The whole stack is developed against ``vcan0`` (virtual CAN) and deployed against a
real ``can0``. Only the config changes — see CLAUDE.md §4. Values are resolved from,
in order of precedence: explicit constructor args, environment variables, defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class CanConfig:
    """Connection settings for a single CAN channel.

    Attributes:
        interface: python-can backend (``socketcan``, ``virtual``, ``pcan``, …).
        channel: Channel name (e.g. ``vcan0``, ``can0``).
        bitrate: Nominal bitrate in bit/s. Ignored by SocketCAN (set via ``ip link``)
            but honored by backends that configure the controller themselves.
        fd: Enable CAN FD (flexible data-rate) frames.
        data_bitrate: CAN FD data-phase bitrate in bit/s; only used when ``fd`` is set.
        receive_own_messages: Loop back frames this node transmits (useful on
            ``virtual`` buses and for self-test).
    """

    interface: str = "socketcan"
    channel: str = "vcan0"
    bitrate: int = 500_000
    fd: bool = False
    data_bitrate: int = 2_000_000
    receive_own_messages: bool = False

    @classmethod
    def from_env(cls, **overrides) -> CanConfig:
        """Build a config from ``CANOPY_CAN_*`` env vars, with kwargs taking priority."""

        def env(name: str, default):
            return os.environ.get(f"CANOPY_CAN_{name}", default)

        def env_bool(name: str, default: bool) -> bool:
            raw = os.environ.get(f"CANOPY_CAN_{name}")
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        d = cls()  # slots=True: read defaults from an instance, not the class descriptors
        base = cls(
            interface=str(env("INTERFACE", d.interface)),
            channel=str(env("CHANNEL", d.channel)),
            bitrate=int(env("BITRATE", d.bitrate)),
            fd=env_bool("FD", d.fd),
            data_bitrate=int(env("DATA_BITRATE", d.data_bitrate)),
            receive_own_messages=env_bool("RECEIVE_OWN_MESSAGES", d.receive_own_messages),
        )
        for key, value in overrides.items():
            if value is not None:
                setattr(base, key, value)
        return base
