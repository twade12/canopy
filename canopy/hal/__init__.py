"""Hardware Abstraction Layer.

Every instrument (CAN, PSU, matrix, scope, current monitor) is a driver behind a
common interface so tests never touch hardware directly (CLAUDE.md §5). Phase 0 ships
only the CAN interface; other drivers arrive in later phases.
"""

from canopy.hal.can_iface import CanInterface

__all__ = ["CanInterface"]
