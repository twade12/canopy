"""Build a :class:`VirtualVehicle` from a platform YAML + DBC.

Vehicles are *data, not code* (CLAUDE.md core principle). A vehicle file names the DBC and
lists the ECUs, their periodic frames (with E2E config), and any UDS personality. This is
the per-platform "car in a box" definition referenced by ``canopy sim run``.
"""

from __future__ import annotations

from pathlib import Path

import cantools
import yaml

from canopy.hal.can_iface import CanInterface
from canopy.sim.e2e import E2EProfile
from canopy.sim.ecu import VirtualEcu
from canopy.sim.uds_server import UdsServerConfig
from canopy.sim.vehicle import VirtualVehicle


def _as_int(value) -> int:
    """Accept ints or hex strings like '0x7E0' from YAML."""
    if isinstance(value, str):
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    return int(value)


def _build_e2e(spec: dict | None) -> E2EProfile:
    if not spec:
        return E2EProfile()
    return E2EProfile(
        counter_signal=spec.get("counter_signal"),
        checksum_signal=spec.get("checksum_signal"),
        algorithm=spec.get("algorithm", "sum8"),
        counter_max=int(spec.get("counter_max", 15)),
    )


def _build_uds(spec: dict | None) -> UdsServerConfig | None:
    if not spec:
        return None
    dtcs = [(_as_int(d["code"]), _as_int(d["status"])) for d in spec.get("dtcs", [])]
    did_map = {_as_int(k): bytes.fromhex(v) for k, v in spec.get("did_map", {}).items()}
    return UdsServerConfig(vin=spec.get("vin"), did_map=did_map, dtcs=dtcs)


def load_vehicle(path: str | Path, iface: CanInterface) -> VirtualVehicle:
    """Construct a vehicle from `path`, transmitting on `iface`."""
    path = Path(path)
    doc = yaml.safe_load(path.read_text())
    dbc_path = (path.parent / doc["dbc"]).resolve()
    db = cantools.database.load_file(str(dbc_path))

    ecus: list[VirtualEcu] = []
    for ecu_spec in doc.get("ecus", []):
        ecu = VirtualEcu(
            name=ecu_spec["name"],
            request_id=_as_int(ecu_spec["request_id"]) if "request_id" in ecu_spec else None,
            response_id=_as_int(ecu_spec["response_id"]) if "response_id" in ecu_spec else None,
            uds_config=_build_uds(ecu_spec.get("uds")),
        )
        for m in ecu_spec.get("messages", []):
            ecu.add_periodic(
                message=db.get_message_by_name(m["message"]),
                signals=dict(m.get("signals", {})),
                period_s=float(m["period_ms"]) / 1000.0,
                e2e=_build_e2e(m.get("e2e")),
                is_extended_id=bool(m.get("extended_id", False)),
            )
        ecus.append(ecu)

    return VirtualVehicle(iface=iface, ecus=ecus, name=doc.get("name", path.stem))
