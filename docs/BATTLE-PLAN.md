# CANOPY — Battle Plan

> How we get from **Phase 0 (done)** to a working software station **and** a prototype
> full-car-simulator bench, as fast as possible. Companion to
> [ARCHITECTURE-NOTES.md](ARCHITECTURE-NOTES.md) and [CLAUDE.md](../CLAUDE.md).

---

## Strategy — three principles that buy speed

1. **`vcan`-first, hardware-last.** Every line of the software station + the entire
   simulator is built and tested on virtual CAN before a relay clicks. Software is never
   blocked on hardware. (This is the whole reason Phase 0 chose SocketCAN.)
2. **Run three tracks in parallel.** Software core (A), simulator (B), and hardware/PCB (C)
   have almost no blocking dependencies for weeks. **Order long-lead items first** — PCB
   fab and parts have 1–3 week lead times, so Track C starts *now* even though it lands last.
3. **Get one platform _correct_ before breadth.** Pick a single reference vehicle with an
   available DBC and known E2E/checksum profile. Depth on one beats shallow on ten — it
   de-risks the hard 40% (counters/CRC/NM) that makes real modules actually respond.

```
Track A  Software station ───────────────────────────────────────────────►
Track B  Virtual vehicle  ──────────────────►(merges into A's restbus)─────►
Track C  Hardware / PCB   ──(BOM+fab now)──────────────►(integrate)─────────►
                          ▲ long-lead items ordered week 1
```

---

## Track A — Software station (canopy core)

Builds the runner, diagnostics, persistence, and diagnosis on top of the Phase 0 HAL.
Every driver ships with a **mock backend** so the runner is testable on `vcan` with no rig.

### A1 — Diagnostics over the bus  *(Phase 1)*
- `hal/isotp.py` (can-isotp), `hal/uds.py` (udsoncan: 0x10/0x19/0x14/0x22/0x31/0x27/0x3E),
  `hal/obd.py` (modes 0x01–0x0A).
- CLI: `canopy uds read-dtc`, `clear-dtc`, `rdbi <did>`; `canopy obd <pid>`.
- **DoD:** read/clear DTCs and RDBI against a simulated UDS server (Track B) on `vcan0`; tests green.

### A2 — Persistence + run record  *(Phase 1)*
- `docker compose` schema: SQLAlchemy models (`Module/Adapter/TestRun/Observation/
  SymptomVector/Case`), Alembic migration, Timescale hypertable for telemetry.
- Wire the existing BLF logger as `TestRun.raw_trace_path`.
- **DoD:** a `monitor`/diagnostic run writes a `TestRun` + `Observation`s + a BLF path to Postgres.

### A3 — Profiles + runner  *(Phases 1–2)*
- `profiles/schema.py` (pydantic) + `canopy validate`; first real module profile YAML.
- `runner/` declarative step engine: power → wake → restbus-up → diagnostics → measure →
  power-down, with **guaranteed power-down on exception** and e-stop hook.
- **DoD:** `canopy run <profile>` executes a full sequence end-to-end on `vcan` + mocked instruments, emits a pass/fail report.

### A4 — Instrument drivers  *(Phase 2, unlocks when Track C parts arrive)*
- `hal/power.py` (Korad/Riden), `hal/current.py` (INA228), later `hal/scope.py`/`dmm.py`.
- Each with a mock backend first; real backend validated on the bench when hardware lands.
- **DoD:** runner sets current-limit-before-energize and logs a current trace (mock, then real).

### A5 — Diagnosis engine + wiki  *(Phase 5, but seed early)*
- `diagnosis/observations.py` (symptom vector), `rules.py` (authored rules), `similarity.py`
  (pgvector NN), `wiki/` markdown export.
- **DoD:** a new run's symptom vector returns ranked past `Case`s + any fired rules; one module's profile + cases export to a wiki page.

### A6 — API + UI  *(Phase 6)*
- FastAPI endpoints (upload/confirm/run/cases) + lightweight frontend.
- **DoD:** a tech can upload a diagram, confirm wiring, run a test, and view a case in the browser.

---

## Track B — Virtual vehicle simulator (`canopy/sim/`)

The crown jewel. Pull forward — it's pure software, and Track A's diagnostics need a
realistic peer to talk to. **This is also the standalone open-source deliverable.**

### B1 — Restbus that real modules accept
- `sim/vehicle.py` + `sim/ecu.py`: load platform DBC, schedule periodic frames at correct
  cycle times across one or more `vcan` channels.
- `sim/e2e.py`: **rolling alive-counter + checksum/CRC** (per-OEM plugin for the reference
  platform). *This is the make-or-break feature.*
- `sim/nm.py`: network management keep-alive + tester-present.
- **DoD:** a real reference module, restbus running, leaves limp/sleep mode and broadcasts normally.

### B2 — Virtual ECUs with UDS personalities
- `sim/ecu.py` gains a UDS responder (answers 0x22/0x19/etc. as the absent module would).
- `vehicles/<platform>.yaml`: which ECUs, which buses, which DBC.
- **DoD:** Track A's UDS client can query a *simulated* peer ECU and get correct responses; the "control the engine/BCM while testing the ECU" demo works on `vcan`.

### B3 — Closed-loop plant + fault injection
- `sim/plant.py` (first-order models: command → plausible feedback) to clear plausibility DTCs.
- `sim/faults.py` (drop/corrupt/delay/stick/bus-off/short) — doubles as a **labeled-data generator** for the diagnosis corpus.
- **DoD:** injecting a defined fault produces a reproducible symptom signature captured as an `Observation`/`Case`.

### B4 — Standalone "virtual vehicle" packaging
- `canopy sim run <platform>` brings up a full virtual car on `vcan`; document connecting an
  external scan tool / OBD app to it.
- **DoD:** a third party can `canopy sim run f150` and scan a "live vehicle" with their own tool.

---

## Track C — Hardware / PCB (full-car-sim bench)

Long lead times → **start week 1**, integrate last. Phase the matrix exactly per CLAUDE.md
§3.4 (manual → relay banks → custom PCB) so we're never blocked on a board spin.

### C0 — Order long-lead items NOW  *(week 1)*
- CAN: 2× **CANable 2.0** (dev, dual-channel `can0`/`can1`) + 1 production-grade
  (**PEAK PCAN-USB FD** or **Kvaser**) for timing comparison.
- Power: **Korad KA3005P** (or Riden RD6006) bench PSU; **INA228** breakout(s).
- Switching (Phase B): **Sequent Microsystems 8-relay HATs** ×2–4 *or* Numato USB relay
  boards; an **RP2040** to drive banks over USB serial.
- Protection: TVS diodes, automotive fuses + holders, reverse-polarity FET/diode, an
  **e-stop** switch wired to cut the DUT rail independent of software.
- Controller: **Raspberry Pi 5 (8 GB)** + Ubuntu 24.04 (self-contained bench).
- (See BOM below.)

### C1 — Manual bench bring-up  *(Phase A matrix — no PCB)*
- Pi 5 + dual CANable as `can0`/`can1`; run **Track B's simulator on real `can0`** into a
  real reference module wired by hand on a breadboard/labeled harness.
- PSU + INA228 logging current via `hal/power.py`/`hal/current.py`.
- **DoD:** real module on the bench, simulator restbus on real CAN, module wakes and we log its current signature. *This is the first real "full car sim drives a real DUT" milestone.*

### C2 — Relay-bank routing + harness identity  *(Phase B matrix)*
- RP2040 + relay HATs implement `hal/matrix.py`; 16–32 switchable channels.
- First adapter harness for the reference module → standard test header; add **harness ID**
  (1-Wire EEPROM / ID resistor / QR) and auto-load the matching profile.
- E-stop interlock verified to cut power independent of host + MCU.
- **DoD:** `canopy run <profile>` closes/open relays automatically and auto-detects the harness.

### C3 — Custom matrix PCB  *(Phase C matrix)*
- KiCad design: tiered header (power/ground/CAN/GP-IO), smart high-side switches
  (PROFET-class) on power pins, relay/FET crosspoint banks, per-rail INA228, TVS/fuse
  protection, RP2040/STM32 controller, e-stop interlock.
- Spin v1 → bring up → fold into `hal/matrix.py`.
- **DoD:** "route any resource to any pin" under software; full plug-and-run for a known module.

### BOM — minimum viable bench (Track C0/C1)
| Item | Suggested part | Role |
|---|---|---|
| Controller | Raspberry Pi 5 8 GB + PSU + SSD | Station host (SocketCAN) |
| CAN ×2 | CANable 2.0 (gs_usb/candleLight, CAN FD) | `can0` restbus / `can1` DUT |
| CAN (prod) | PEAK PCAN-USB FD *or* Kvaser Leaf | Timing-grade reference |
| Bench PSU | Korad KA3005P (or Riden RD6006) | Programmable DUT supply |
| Current | INA228 breakout ×1–2 | High-side current signatures |
| Relays | Sequent 8-relay HAT ×2 (or Numato USB) | Phase-B switching |
| MCU | RP2040 board | Drives relays / reads harness ID |
| Protection | TVS, fuses+holders, reverse-polarity FET | DUT rail safety |
| Safety | E-stop switch + contactor/relay | Cuts power independent of SW |
| Misc | 40–64-pin headers, ID EEPROM/1-Wire, wiring | Test header + harness |

---

## Critical path & sprint cadence (2-week sprints)

```
Wk 1  ┌ A1 isotp/uds/obd        ┌ B1 restbus+E2E+NM        ┌ C0 ORDER PARTS (long-lead)
Wk 2  └ A2 persistence/models   └ (B1 cont.)               └ (parts shipping)
Wk 3  ┌ A3 profiles+runner      ┌ B2 virtual-ECU UDS        ┌ C1 manual bench bring-up
Wk 4  └ (A3 cont., run report)  └ (B2 cont.)               └ (real module wakes on sim)
Wk 5  ┌ A4 power/current driver ┌ B3 plant + fault inject   ┌ C2 relay matrix + harness ID
Wk 6  └ A5 diagnosis seed+wiki  └ B4 standalone sim package  └ (e-stop interlock verified)
Wk 7+ ┌ A6 API/UI               ┌ (sim breadth: 2nd platform)┌ C3 custom matrix PCB spin
```

- **Hard dependency:** A1 (UDS client) ⇄ B2 (UDS server) — build them against each other on
  `vcan` in the same sprint; they validate each other for free.
- **Soft dependency:** A4 real backends and all of Track C unlock as parts arrive — until
  then, mocks keep Track A fully testable.
- **First "wow" demo (target end of Wk 4):** simulator runs a full virtual car on `vcan`;
  a real module on the bench (C1) wakes from the simulator's restbus on real CAN; UDS reads
  its DTCs. That single demo proves the entire thesis.

---

## Definition of done (program level)
- A tech plugs a known module on a harness → station auto-detects it, energizes safely,
  runs the sequence, and emits a pass/fail report with **ranked component-level causes**.
- Every run persists a `TestRun` + `Observation`s + BLF trace + (when labeled) a `Case`.
- `canopy sim run <platform>` stands up a controllable virtual vehicle on `vcan` that an
  external scan tool sees as live.

---

## Risk register
| Risk | Impact | Mitigation |
|---|---|---|
| E2E checksum/CRC algorithm unknown for chosen platform | Real modules won't accept restbus | **Pick the reference platform by data availability** (DBC + known E2E). De-risk in B1, Wk 1. |
| Security access (0x27) seed→key gated | Some UDS services unreachable | Pluggable seed→key provider; scope v1 to non-secured services; right-to-repair framing only. |
| DBC/DID data scarcity for breadth | Slow platform coverage | Depth-first on one platform; CBM's real-module runs become the proprietary corpus (the moat). |
| Hardware lead times | Track C slips | Order Wk 1; keep all software on mocks/`vcan`; manual bench (C1) needs no PCB. |
| Matrix complexity/cost | PCB over-scope | Tiered pins + harness library, not a full N×M crosspoint; phase A→B→C. |
| Safety incident on energize | Damaged cores / injury | Hardware e-stop + reverse-polarity + per-rail fuse + current-limit-before-energize + audit log; confirm-before-energize gate. |

---

## Immediate next actions (this week)
1. **Track C0:** place the long-lead orders (CANables, PSU, INA228, relay HATs, RP2040, Pi 5, e-stop, protection parts).
2. **Pick the reference platform** — choose by DBC + E2E availability; record it in ARCHITECTURE-NOTES §6.
3. **Track B1 + A1 together:** stand up `sim/` restbus (with E2E counters/CRC + NM) and the UDS client/server pair on `vcan0`, validating each other.
4. **Track A2:** land the SQLAlchemy schema + first migration so runs persist from the start (the data compounds from day one).
