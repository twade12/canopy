"""Virtual-vehicle restbus tests: scheduling, alive-counters, and checksums."""

from __future__ import annotations

from pathlib import Path

import cantools

from canopy.config import CanConfig
from canopy.hal.can_iface import CanInterface
from canopy.sim.e2e import CHECKSUM_ALGORITHMS, E2EProfile, crc8_j1850
from canopy.sim.ecu import VirtualEcu
from canopy.sim.loader import load_vehicle
from canopy.sim.vehicle import VirtualVehicle

DBC = Path(__file__).parents[1] / "dbc" / "ford_f250_powertrain.dbc"
VEHICLE = Path(__file__).parents[1] / "vehicles" / "ford_f250_6.7.yaml"


def test_checksum_algorithms_are_deterministic() -> None:
    payload = bytes([0x11, 0x22, 0x33, 0x44])
    assert CHECKSUM_ALGORITHMS["xor8"](payload) == 0x11 ^ 0x22 ^ 0x33 ^ 0x44
    assert CHECKSUM_ALGORITHMS["sum8"](payload) == (0x11 + 0x22 + 0x33 + 0x44) & 0xFF
    # CRC-8/SAE-J1850 known vector for b"123456789" is 0x4B.
    assert crc8_j1850(b"123456789") == 0x4B


def test_e2e_roundtrip_verifies() -> None:
    db = cantools.database.load_file(str(DBC))
    msg = db.get_message_by_name("PCM_Powertrain")
    e2e = E2EProfile("AliveCounter", "Checksum", "crc8_j1850", 15)
    data = e2e.encode(msg, {"EngineRPM": 800, "VehicleSpeed": 0}, counter=3)
    assert e2e.verify(msg, data)
    decoded = msg.decode(data, decode_choices=False)
    assert decoded["AliveCounter"] == 3
    # Corrupting a byte breaks verification.
    bad = bytearray(data)
    bad[0] ^= 0xFF
    assert not e2e.verify(msg, bytes(bad))


def test_restbus_transmits_with_incrementing_counter(can_config: CanConfig) -> None:
    db = cantools.database.load_file(str(DBC))
    msg = db.get_message_by_name("PCM_Powertrain")
    e2e = E2EProfile("AliveCounter", "Checksum", "crc8_j1850", 15)

    with CanInterface(can_config) as tx, CanInterface(can_config) as rx:
        vehicle = VirtualVehicle(tx)
        pcm = VirtualEcu("PCM")
        pcm.add_periodic(msg, {"EngineRPM": 800, "VehicleSpeed": 0}, 0.01, e2e)
        vehicle.add_ecu(pcm)

        vehicle.reset_schedule(0.0)
        for now in (0.0, 0.02, 0.04):       # three cycle times elapse
            vehicle.tick(now)
        frames = list(rx.monitor(timeout=1.0, limit=3))

    assert len(frames) == 3
    counters = []
    for f in frames:
        assert f.arbitration_id == 0x100
        assert e2e.verify(msg, bytes(f.data))           # checksum valid on every frame
        counters.append(msg.decode(bytes(f.data), decode_choices=False)["AliveCounter"])
    assert counters == [0, 1, 2]                          # alive-counter advances


def test_load_vehicle_from_yaml(can_config: CanConfig) -> None:
    with CanInterface(can_config) as iface:
        vehicle = load_vehicle(VEHICLE, iface)
    assert vehicle.name == "ford_f250_6.7"
    names = {ecu.name for ecu in vehicle.ecus}
    assert names == {"PCM", "TCM", "BCM"}
    pcm = next(e for e in vehicle.ecus if e.name == "PCM")
    assert pcm.request_id == 0x7E0
    assert pcm.uds_config is not None
    assert pcm.messages[0].e2e.algorithm == "crc8_j1850"
