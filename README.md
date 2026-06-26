# CANOPY

**Universal CAN Module Test & Diagnostic Station** for Circuit Board Medics.

Plug an automotive ECU/module onto the bench, pick its profile, hit run — the station
powers it, simulates the rest of the vehicle bus (restbus), runs diagnostics over
CAN / CAN FD / UDS / OBD-II / J1939, measures power and signal behavior, and produces a
pass/fail report with ranked component-level root causes. Every run becomes a structured
record that compounds into the internal repair wiki.

See [CLAUDE.md](CLAUDE.md) for the full architecture and roadmap.

---

## Status: Phase 0 — Bus MVP

This is the zero-hardware foundation. It works entirely against a **virtual CAN bus**,
so the whole stack is testable before a single relay clicks.

Shipped in Phase 0:

- `canopy/hal/can_iface.py` — backend-agnostic `python-can` wrapper (SocketCAN by default,
  any backend via config). The only HAL driver in this phase.
- `canopy/decode.py` — `cantools` signal-level DBC decode.
- `canopy/trace.py` — Vector-compatible **BLF** raw-trace logging.
- `canopy/cli.py` — `send`, `monitor`, `decode` commands.
- `tests/` — round-trip + decode tests that run against `vcan0`, falling back to
  python-can's in-process `virtual` backend on CI.
- `docker-compose.yml` — Postgres + TimescaleDB + pgvector (provisioned now, schema in Phase 1).

Not yet implemented (later phases): UDS/OBD diagnostics, restbus, PSU/current/matrix/scope
drivers, profiles, vision pipeline, diagnosis engine, web UI.

---

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python ≥ 3.10 on Linux (SocketCAN).

---

## Creating `vcan0` (virtual CAN) locally

SocketCAN ships a virtual CAN driver. Bring up a `vcan0` interface and the entire stack
runs with no hardware:

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# verify
ip -details link show vcan0
```

Tear it down with:

```bash
sudo ip link set down vcan0
sudo ip link delete vcan0
```

Inspect traffic with `can-utils` (separate package: `sudo apt install can-utils`):

```bash
candump vcan0          # in one terminal
cansend vcan0 123#01020304   # in another
```

> **CI / no privileges:** the test suite auto-detects whether `vcan0` is available and
> falls back to python-can's in-process `virtual` backend, so `pytest` passes without
> `sudo` or kernel modules.

---

## CLI usage

```bash
# Send a frame (id and payload are hex)
canopy send vcan0 123 01020304

# Watch the bus for 5s, decoding against a DBC, and save a BLF trace
canopy monitor vcan0 --timeout 5 --dbc dbc/platform.dbc --trace

# Decode a recorded BLF trace
canopy decode traces/20260626T184500Z_monitor.blf --dbc dbc/platform.dbc
```

A quick self-test loop on one terminal pair:

```bash
canopy monitor vcan0 --timeout 10 &   # listen
canopy send vcan0 123 deadbeef        # transmit
```

Configuration can also come from the environment (`CANOPY_CAN_INTERFACE`,
`CANOPY_CAN_CHANNEL`, `CANOPY_CAN_BITRATE`, `CANOPY_CAN_FD`, …); CLI flags win.

---

## Database (provisioned now, used from Phase 1)

```bash
docker compose up -d db      # Postgres + TimescaleDB + pgvector on :5432
```

Default credentials: `canopy` / `canopy`, database `canopy`. The init script enables the
`timescaledb` and `vector` extensions on first boot.

---

## Tests & lint

```bash
pytest        # runs against vcan0 if present, else the virtual backend
ruff check .
```

---

## Deploying on real hardware

Develop on `vcan0`, deploy on `can0`. Bring up a real CANable/PEAK/Kvaser SocketCAN
device and point the config at it — no code changes:

```bash
sudo ip link set can0 up type can bitrate 500000
canopy monitor can0 --timeout 5
```
