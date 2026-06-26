"""Test fixtures for the CAN stack.

The whole point of SocketCAN ``vcan`` is that Phase 0 is fully testable with zero
hardware (CLAUDE.md §4, §9). We prefer a real ``vcan0`` when the kernel module is
loadable, and otherwise fall back to python-can's in-process ``virtual`` backend so the
identical tests run on CI with no privileges and no hardware.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from canopy.config import CanConfig

VCAN_CHANNEL = "vcan0"


def _vcan0_is_up() -> bool:
    """True if a ``vcan0`` link already exists and is up."""
    if shutil.which("ip") is None:
        return False
    result = subprocess.run(
        ["ip", "-br", "link", "show", VCAN_CHANNEL],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _try_bring_up_vcan0() -> bool:
    """Best-effort: load the module and create ``vcan0``. Returns success.

    Requires privileges; silently fails (and the suite falls back to ``virtual``) when
    run unprivileged, e.g. on CI.
    """
    if _vcan0_is_up():
        return True
    if shutil.which("ip") is None:
        return False
    cmds = [
        ["modprobe", "vcan"],
        ["ip", "link", "add", "dev", VCAN_CHANNEL, "type", "vcan"],
        ["ip", "link", "set", "up", VCAN_CHANNEL],
    ]
    for cmd in cmds:
        # Try unprivileged first, then with sudo -n (non-interactive) if available.
        if subprocess.run(cmd, capture_output=True).returncode == 0:
            continue
        if shutil.which("sudo") and subprocess.run(
            ["sudo", "-n", *cmd], capture_output=True
        ).returncode == 0:
            continue
        return False
    return _vcan0_is_up()


@pytest.fixture(scope="session")
def can_config() -> CanConfig:
    """A working CAN config: real ``vcan0`` if available, else ``virtual``.

    Both backends loop transmitted frames back to other buses on the same channel, so
    send/receive round-trips work either way.
    """
    if _try_bring_up_vcan0():
        return CanConfig(
            interface="socketcan",
            channel=VCAN_CHANNEL,
            receive_own_messages=True,
        )
    return CanConfig(
        interface="virtual",
        channel="canopy-test",
        receive_own_messages=True,
    )
