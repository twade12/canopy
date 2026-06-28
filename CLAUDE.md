# CANOPY — Universal CAN Module Test & Diagnostic Station

> **Save this as `CLAUDE.md` (or `PROJECT_BRIEF.md`) in the repo root.**
> It is the single source of truth for the project. Claude Code should read this
> first on every session and keep it updated as architecture evolves.

**CAN-Anchored Reliability & Anomaly Recording sYstem.** An internal bench tool for
Circuit Board Medics that automates testing, restbus simulation, and component-level
fault diagnosis of automotive ECUs and modules communicating over CAN / CAN FD /
J1939 — and accumulates every test into a structured knowledge base that becomes the
internal repair wiki.

---

## 0. Companion docs & current status (read these too)

The vision/triage app is live and substantial (`canopy/vision/`): wiring-diagram→pinout,
board-photo→components (editable boxes, corrections, multi-photo), grounded Triage, a physics-first
**Guided** walkthrough (streams its reasoning), a 33-article house **Knowledge** base, Memories,
**Wiki** export, phone capture, a **Bench** CAN tab, and a **Profile** tab. Postgres/pgvector
optional; systemd + nginx deploy.

**CAB (Car-in-a-Box)** is the physical 10-slot HIL bench this software drives. Canopy is the brain,
CAB is the body, and the **Module Profile** (`canopy/profiles/`) is the seam: diagram/PCB →
auto-drafted profile → confirm → CAB executes. Durable plans:
- [`docs/CAB-INTEGRATION.md`](docs/CAB-INTEGRATION.md) — the CAB↔Canopy north star + roadmap (tiers).
- [`docs/CAB-PROTOCOL.md`](docs/CAB-PROTOCOL.md) — the host↔CAB serial command protocol (v1).
- [`docs/GUIDED-TRIAGE.md`](docs/GUIDED-TRIAGE.md) — the guided-walkthrough design.
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) — new-user tour of the tabs.
- `canopy/profiles/` (schema + auto-draft), `canopy/hal/cab.py` (CAB client + mock bench).

---

## 1. North-Star Goals

1. **Plug a module onto the bench, pick its profile, hit run** → the station powers
   it correctly, wakes it, simulates the rest of the vehicle bus (restbus), runs
   diagnostics over CAN/UDS/OBD-II, measures power and signal behavior, and produces
   a pass/fail report with a **ranked list of most-likely component-level root causes**.
2. **Upload a screenshot of a wiring diagram** → the station parses the connector
   pinout with vision, maps it to the standard test header, and tells the tech exactly
   which adapter-harness pins go where (with a mandatory human confirm-before-energize step).
3. **Every test run becomes a structured record.** Symptom signatures → root causes
   accumulate over time, drive similarity-based diagnosis for new modules, and export
   directly to the internal wiki.
4. **Hardware-agnostic and module-agnostic.** New adapters, new CAN interfaces, new
   instruments, and new modules are added through configuration and small driver
   plugins — never by rewriting the core.

---

## 2. The "Universal Interface" — How It Actually Works

There is no single magic connector. The universal interface is three layers:

```
  Module connector  ──►  Adapter harness  ──►  Standard test header  ──►  Switch matrix  ──►  Station resources
  (per-module)           (per-module,            (fixed, e.g. 40-pin)     (relay/FET,          (12V, GND, CAN-H/L,
                          cheap, library)                                  16–32 ch)            wake lines, loads,
                                                                                                measurement channels)
```

- **Station resources** are fixed: regulated 12V (KL30), switched ignition (KL15),
  ground, CAN-H/CAN-L (one or more channels), wake/enable lines, programmable loads,
  and measurement taps.
- **Switch matrix** routes those resources to any pin on the **standard test header**
  under software control.
- **Adapter harness** maps a specific module's connector to the standard test header.
  Each module type gets one harness (built once, kept in a library). This is the
  natural home for **PDP-Connect** as the station-side keyed interface.
- A **module profile** (YAML) describes, for each module: connector pinout, which
  header pins carry power/ground/CAN/wake, power sequencing, restbus requirements,
  diagnostic sequences, and pass/fail criteria.

The wiring-diagram vision feature exists to **generate the adapter-harness mapping and
the module profile** from a screenshot, instead of transcribing pinouts by hand.

---

## 3. Hardware Requirements

### 3.1 Station controller
- **Recommended:** Raspberry Pi 5 (8 GB) *or* a small fanless x86 Linux mini-PC.
  Linux is required for SocketCAN. The Pi keeps the station self-contained; the mini-PC
  gives more headroom for the DB + vision pipeline. Either works.
- OS: Ubuntu 24.04 LTS (or Raspberry Pi OS 64-bit).

### 3.2 CAN interface(s)
- **Dev / MVP:** CANable 2.0 (`gs_usb`/candleLight firmware, CAN FD, ~$50). Shows up
  as a native SocketCAN device.
- **Production:** PEAK **PCAN-USB FD** or **Kvaser** (Leaf / USBcan Pro). Both have
  excellent SocketCAN drivers and rock-solid timing.
- **Multi-channel** (needed for restbus on one bus while talking to the DUT on another,
  or bridging): Kvaser **USBcan Pro 2xHS** or PCAN-USB **Pro FD** (2 channel). Or run
  two CANable adapters as `can0` / `can1`.
- Avoid relying on MCP2515 SPI HATs for production — they're fine for a second channel
  but timing/buffering is limiting. MCP2518FD HATs are acceptable for CAN FD on a Pi.

### 3.3 Power & current sensing (first-class diagnostic data)
- **Programmable bench PSU with remote control:** Korad KA3005P (SCPI-ish over USB
  serial) or Riden RD6006 (Modbus RTU). Set voltage/current limits and read back draw.
- **High-side current monitor:** INA228 (or INA226) over I²C for fast, high-resolution
  current logging — quiescent, sleep, inrush, and per-state current signatures. This
  catches a large fraction of component faults independent of CAN.
- **Reverse-polarity + fusing** on the DUT supply rail. Non-negotiable for protecting cores.

### 3.4 Switch matrix (the hard part — phase it in)
- **Phase A (manual):** breadboard / labeled adapter harness, no matrix. Tech wires by hand.
- **Phase B (relay banks):** stackable relay HATs (Sequent Microsystems 8-relay HATs)
  or USB relay boards (Numato), or an RP2040/ESP32 driving relay banks over USB serial.
  Target 16–32 switchable channels.
- **Phase C (custom matrix PCB):** your own KiCad-designed relay/FET crosspoint board.
  This is where the station becomes truly "route any resource to any pin."

### 3.5 Measurement (optional but high-value)
- **Analog rails / DAQ:** LabJack T7 (great API, lots of channels) or an MCC USB DAQ
  (`uldaq` on Linux), or an ADC HAT for budget.
- **Waveform capture:** SCPI-controllable scope (Rigol DS1000Z, Siglent SDS) via PyVISA
  for CAN-H/CAN-L differential integrity — ringing/asymmetry points straight at a failing
  transceiver or termination.
- **Precision DMM** with SCPI for rail and continuity checks.

### 3.6 Wake / ignition / e-stop
- Relays for KL15 (ignition) and any module-specific enable/wake lines, switchable by software.
- **Physical e-stop** that cuts DUT power independent of software. Required.

---

## 4. Software Stack

| Concern | Library / Tool | Notes |
|---|---|---|
| CAN transport | `python-can` | SocketCAN, PCAN, Kvaser, slcan, vector backends |
| ISO-TP (15765-2) | `can-isotp` | Multi-frame transport for UDS/OBD |
| UDS (ISO 14229) | `udsoncan` | DTC read/clear, RDBI, routine control, security access |
| DBC encode/decode | `cantools` | Signal-level encode/decode; drives restbus generation |
| OBD-II | direct over `can-isotp` (preferred) or `python-OBD` | ELM327 interop optional |
| J1939 (diesel/heavy) | `can-j1939` | For diesel modules you flagged; profile dimension |
| Instruments | `pyvisa`, `pyserial`, `minimalmodbus` | Scope/DMM/PSU/relay control |
| Current monitor | `smbus2` / vendor lib | INA228 over I²C |
| Data store | PostgreSQL + **TimescaleDB** + **pgvector** | Time-series traces + symptom-vector retrieval |
| Raw trace logging | `python-can` ASC/BLF writers | Vector-compatible logs per run |
| API / orchestration | FastAPI + asyncio | Concurrent CAN listen + instrument control |
| Vision (wiring diagram) | Anthropic API (Claude vision) | Structured-output pinout extraction |
| Web UI | FastAPI + lightweight frontend | Upload, confirm wiring, run tests, view reports |
| Config | YAML (module profiles, restbus, matrix map) | Mirrors your MNEMOS/Mandrel corpus pattern |

**Why SocketCAN/Linux:** `bring up` a real or virtual bus with
`ip link set can0 up type can bitrate 500000`, and develop the *entire* stack against
`vcan0` (virtual CAN) with zero hardware. `python-can`, `can-isotp`, and `udsoncan`
are all first-class on SocketCAN. Develop on `vcan0`, deploy on `can0`.

---

## 5. System Architecture

```
                         ┌─────────────────────────────┐
                         │           Web UI / CLI       │
                         │  upload diagram · run tests  │
                         │  confirm wiring · view cases │
                         └──────────────┬──────────────┘
                                        │ FastAPI
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
        ┌───────▼───────┐      ┌────────▼────────┐     ┌────────▼────────┐
        │  Test Runner  │      │ Diagnosis Engine│     │ Vision Pipeline │
        │  (sequencer)  │      │ symptom→cause   │     │ diagram→pinout  │
        └───────┬───────┘      └────────┬────────┘     └────────┬────────┘
                │                       │                       │
        ┌───────▼───────────────────────▼───────────────────────▼───────┐
        │                  Module Profiles (YAML)                       │
        └───────┬───────────────────────────────────────────────────────┘
                │
        ┌───────▼───────────── Hardware Abstraction Layer (HAL) ─────────┐
        │  CAN driver │ UDS/OBD │ Restbus │ PSU │ Current │ Matrix │ Scope │
        └───────┬───────────────────────────────────────────────────────┘
                │
        ┌───────▼───────┐                    ┌──────────────────────────┐
        │  Bench HW     │                    │  Postgres + Timescale +  │
        │  (DUT + instr)│◄──── logs ────────►│  pgvector (cases/traces) │
        └───────────────┘                    └──────────────────────────┘
```

### Core principles
- **HAL isolates hardware.** Every instrument (CAN, PSU, matrix, scope, current
  monitor) is a driver implementing a common interface. Tests never touch hardware
  directly. Swapping a CANable for a Kvaser is a config change.
- **Profiles are data, not code.** A module's pinout, power sequence, restbus needs,
  test steps, and pass/fail thresholds live in YAML. Adding a module = adding a profile.
- **Everything is logged.** Every run writes a raw CAN trace (BLF/ASC), instrument
  telemetry to Timescale, and a structured `Case` record.

---

## 6. Data Model (the part that compounds)

```
Module          (make, model, part_number, connector, profile_ref)
Adapter         (module_ref, header_pin_map, harness_id)
TestRun         (module_ref, timestamp, profile_version, raw_trace_path, result)
Observation     (run_ref, type, value)        # missing CAN IDs, DTCs, current draw,
                                              #   rail voltages, waveform anomalies
SymptomVector   (run_ref, embedding)          # pgvector: feature vector of observations
Case            (run_ref, root_cause,          # COMPONENT-LEVEL: "U3 5V LDO open",
                 component_ref, repair_action, #   "CAN transceiver TXD stuck low",
                 confidence, technician)       #   "corroded pin 12", "Q5 shorted"
```

**Diagnosis loop:** a new DUT's `SymptomVector` is matched (pgvector nearest-neighbor)
against historical `Case` records → returns ranked likely root causes with confidence,
*plus* any deterministic rules that fired. The labeled `Case` records are simultaneously
(a) the diagnosis training data and (b) the wiki content.

---

## 7. Key Subsystems

### 7.1 Restbus simulation
Load the vehicle-platform DBC with `cantools`, send the periodic frames that *absent*
ECUs would broadcast (gateway heartbeat, ignition status, network management) so the
DUT leaves limp/sleep mode and behaves as if installed. Stored as per-platform restbus
YAML referencing the DBC.

### 7.2 UDS / OBD-II diagnostics
- **Station as tester (primary):** send UDS services over ISO-TP — read/clear DTCs
  (0x19/0x14), ReadDataByIdentifier (0x22), RoutineControl (0x31), security access
  (0x27) where applicable. OBD-II modes 0x01–0x0A as a subset.
- **Station as gateway (advanced, later):** present expected responses so a tech's
  external OBD-II scan tool plugged onto the bench bus sees a "live vehicle."

### 7.3 Wiring-diagram vision pipeline
```
upload image → preprocess (deskew/crop) → Claude vision (structured JSON):
   { connector, pins: [{ pin, signal, wire_color, mating }] }
   → validate against existing profile (if any)
   → map signals to station resources, route to header via matrix config
   → emit: (a) human-readable connection list, (b) matrix routing commands,
           (c) draft module profile
   → ⚠ HUMAN CONFIRM-BEFORE-ENERGIZE (verify power & ground pins manually) ⚠
```
Vision parses of wiring diagrams are **never** trusted to auto-energize. The tech
confirms power/ground/CAN assignments in the UI before the matrix closes any relay.

### 7.4 Failure-mode learning (phased, not ML-first)
1. **Rules YAML:** authored symptom→cause rules (e.g., "no 5V rail + no CAN ACK →
   suspect main LDO"). Grows as techs encode knowledge.
2. **Similarity retrieval:** pgvector over symptom vectors returns nearest past cases.
3. **Classifier (later):** once enough labeled `Case` data exists, train a model that
   outputs ranked root causes. The data has been accumulating from day one.

### 7.5 Wiki export
Each module profile + its resolved `Case` records render to markdown pages
(pinout, known failure modes, ranked causes, repair actions) for the internal wiki.

---

## 8. Repository Structure

```
canopy/
├── CLAUDE.md                      # this file
├── pyproject.toml
├── docker-compose.yml             # postgres + timescale + pgvector
├── canopy/
│   ├── hal/                       # hardware abstraction
│   │   ├── can_iface.py
│   │   ├── uds.py  obd.py  j1939.py
│   │   ├── restbus.py
│   │   ├── power.py               # PSU drivers (Korad, Riden)
│   │   ├── current.py             # INA228
│   │   ├── matrix.py              # relay/FET switch matrix
│   │   └── scope.py  dmm.py       # PyVISA instruments
│   ├── profiles/
│   │   ├── schema.py              # pydantic models for profile YAML
│   │   └── modules/*.yaml         # per-module profiles
│   ├── restbus/*.yaml             # per-platform restbus configs
│   ├── runner/                    # test sequencer + pass/fail
│   ├── diagnosis/                 # rules engine + pgvector retrieval
│   ├── vision/                    # wiring-diagram pipeline (Anthropic API)
│   ├── data/                      # SQLAlchemy models, Timescale, pgvector
│   ├── wiki/                      # markdown export
│   ├── api/                       # FastAPI app
│   └── cli.py
├── ui/                            # lightweight web frontend
├── dbc/                           # platform DBC files
├── traces/                        # raw BLF/ASC logs
└── tests/                         # pytest, runs against vcan0
```

---

## 9. Phased Roadmap

| Phase | Deliverable | Validates |
|---|---|---|
| **0 — Bus MVP** | `vcan0` dev loop; send/receive; `cantools` DBC decode; BLF logging; CLI | The stack works with zero hardware |
| **1 — Diagnostics** | UDS/OBD over ISO-TP; DTC read/clear; restbus sim; Postgres logging | Real module talks back |
| **2 — Power & profiles** | PSU control + INA228 current logging; power sequencing; module-profile YAML | Automated, safe energize |
| **3 — Matrix** | Relay matrix + adapter-harness library; automated pin routing | "Plug and run" for known modules |
| **4 — Vision** | Wiring-diagram → pinout → draft profile (HITL confirm) | New modules onboarded fast |
| **5 — Learning** | Rules engine + pgvector similarity; wiki export | Ranked root causes; wiki populates |
| **6 — Scale** | Web UI, multi-DUT, gateway-mode OBD, trained classifier | Production internal tool |

Build and ship Phase 0 end-to-end before touching hardware. The whole point of
SocketCAN `vcan` is that the software is fully testable before a single relay clicks.

---

## 10. Safety (protects cores and people)

- Hardware e-stop cuts DUT power independent of software.
- Reverse-polarity protection + per-rail fusing on the DUT supply.
- PSU current limit set per profile **before** energize.
- **Confirm-before-energize:** the matrix never closes power/ground relays from an
  unverified vision parse. The tech verifies pin assignments first.
- Log every energize event, current spike, and matrix state for forensic traceability.

---

## 11. Open Decisions (resolve with Tom)

- Controller: Pi 5 (self-contained) vs. mini-PC (more headroom)?
- Production CAN interface: PEAK vs. Kvaser (multi-channel needs)?
- Matrix path: how many channels for Phase B, and does PDP-Connect become the
  station-side standard header?
- Vision: Anthropic API (cloud) acceptable for diagram parsing, or local model required
  for IP/data-handling reasons?
- Scope of J1939 in v1 given the diesel-module roadmap?

---

## 12. Initial Claude Code Kickoff Prompt

Paste this to start the first session:

> Read `CLAUDE.md`. Scaffold the canopy repo per §8. Set up `pyproject.toml` with
> `python-can`, `can-isotp`, `udsoncan`, `cantools`, `fastapi`, `pydantic`,
> `sqlalchemy`, `psycopg`, and dev deps (`pytest`, `ruff`). Add `docker-compose.yml`
> for Postgres with the TimescaleDB and pgvector extensions. Implement **Phase 0**
> only: a `hal/can_iface.py` wrapping `python-can` (SocketCAN backend, configurable),
> a `cantools`-based decode utility, a BLF logger, and a `cli.py` with `send`,
> `monitor`, and `decode` commands. Write `tests/` that run against a `vcan0`
> virtual bus (include a fixture that brings `vcan0` up, or mocks it on CI). Provide
> a README section on creating `vcan0` locally. Do not add hardware drivers beyond
> the CAN interface yet. Stop after Phase 0 and summarize what's testable without hardware.
