"""Software-defined virtual vehicle — the "car in a box".

Every module that is *not* on the bench becomes a controllable virtual ECU, broadcasting
the periodic frames (with correct alive-counters and checksums) and answering the
diagnostic requests that the absent module would. The device under test cannot tell the
simulated car from a real one.

Runs entirely on (v)CAN — see docs/ARCHITECTURE-NOTES.md §4 and docs/BATTLE-PLAN.md Track B.
"""

from canopy.sim.ecu import PeriodicMessage, VirtualEcu
from canopy.sim.vehicle import VirtualVehicle

__all__ = ["VirtualVehicle", "VirtualEcu", "PeriodicMessage"]
