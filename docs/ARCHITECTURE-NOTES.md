# CANOPY — Architecture Notes

> Companion to [CLAUDE.md](../CLAUDE.md). CLAUDE.md is the canonical brief; this file
> captures the deeper design reasoning for the three things that aren't fully specified
> there yet: the **complete subsystem build-out**, the **physical universal interface
> (custom PCB)**, and the **full-car simulator**. See [BATTLE-PLAN.md](BATTLE-PLAN.md)
> for how/when we build it.

---

## 1. Recap: the universal interface is three layers, not one connector

```
 Module connector ─► Adapter harness ─► Standard test header ─► Switch matrix ─► Station resources
  (per-module)        (per-module,         (fixed, e.g.            (relay/FET,      (12V, GND, CAN-H/L,
                       cheap, library)      40–64-pin)              banks)           wake, loads, taps)
```

The genericity comes from splitting *per-module cost* (a cheap adapter harness) from the
*fixed, expensive infrastructure* (header + matrix + resources). Adding a module =
adding a YAML profile + a harness, never rewriting core. Software-side, the same idea is
the **HAL**: every instrument hides behind a common interface, every driver has a
simulated backend, and tests never touch hardware.

---

## 2. Complete subsystem build-out (the gap between Phase 0 and a real station)

Each is a HAL driver or subsystem package per [CLAUDE.md §8], with a **mock/simulated
backend** so the runner stays `vcan`-testable end-to-end (exactly like `can_iface` today).

### Transport & protocol (Phase 1)
- `hal/isotp.py` — ISO-TP (15765-2) over `can-isotp`; multi-frame transport for UDS/OBD.
- `hal/uds.py` — `udsoncan` client: 0x10 session, 0x19/0x14 DTC read/clear, 0x22 RDBI,
  0x31 RoutineControl, **0x27 security access** with a pluggable seed→key provider,
  0x3E tester-present.
- `hal/obd.py` — OBD-II modes 0x01–0x0A (standardized PIDs; no DBC needed).
- `hal/j1939.py` — `can-j1939` for diesel/heavy modules (PGN/SPN); a profile dimension.

### Instruments (Phase 2) — common `Instrument` protocol + mock backend each
- `hal/power.py` — PSU drivers (Korad KA3005P SCPI, Riden RD6006 Modbus). Set V,
  **current-limit-before-energize**, read-back draw.
- `hal/current.py` — INA228/INA226 over I²C (`smbus2`): quiescent/sleep/inrush/per-state
  current signatures. Highest diagnostic yield per dollar; catches many faults sans CAN.
- `hal/scope.py`, `hal/dmm.py` — PyVISA SCPI (CAN-H/L differential integrity; rails/continuity).
- `hal/matrix.py` — switch-matrix driver (see §3).

### Profiles & sequencing (Phases 1–3)
- `profiles/schema.py` — pydantic models for module-profile YAML (pinout, header map,
  power sequence, restbus ref, diagnostic steps, pass/fail thresholds) + `canopy validate`.
- `profiles/modules/*.yaml`, `restbus/*.yaml` — the libraries.
- `runner/` — declarative step engine: power-on → wake → restbus-up → diagnostics →
  measure → power-down. Per-step pass/fail, structured result, **e-stop integration**,
  and a **guaranteed power-down on any exception**.

### Persistence & logging (Phase 1)
- `data/models.py` — SQLAlchemy: `Module / Adapter / TestRun / Observation /
  SymptomVector / Case`.
- `data/timeseries.py` — Timescale hypertables for telemetry; `data/vectors.py` — pgvector
  store + nearest-neighbor query. Alembic migrations. BLF logger (exists) wired into every run.

### Diagnosis engine (Phase 5)
- `diagnosis/observations.py` — extract a symptom/feature vector (missing CAN IDs, DTC set,
  current-signature features, rail anomalies, waveform metrics).
- `diagnosis/rules.py` — authored, explainable symptom→cause rules in YAML (ships first).
- `diagnosis/similarity.py` — pgvector retrieval → ranked causes + confidence.
- `diagnosis/classifier.py` — trained model, later, once labeled data accumulates.

### Vision, safety, API/UI, quality (cross-cutting)
- `vision/pipeline.py` — image preprocess → Claude vision **structured output** (pydantic
  pinout) → profile draft → matrix routing → **confirm-before-energize gate**. Use the
  latest Claude model; validate against existing profile when present.
- `safety/` — e-stop monitor, energize interlock, per-rail fuse/limit checks, audit log of
  every energize/matrix event.
- `api/` (FastAPI + asyncio), `ui/` (upload/confirm/run/view), `wiki/` (markdown export).
- **Dev/CI** — GitHub Actions (ruff + pytest on virtual backend), pre-commit, coverage,
  type-checking (mypy/pyright), `traces/` retention policy.

---

## 3. Physical universal interface — the custom PCB

Goal: any proprietary module plug → one fixed interface the Pi/PC reads. Solved by the
matrix board + a smart harness library.

### Standard test header (fixed) — tiered pin classes
No cheap pin can be all things at once, so the header has pin *classes*:
- **Power pins** (few): switched 12V/KL30 + KL15, rated for inrush (target 10–20 A), each
  behind a **smart high-side switch** (Infineon PROFET-class) for current limit + e-fuse +
  diagnostics.
- **Ground/return pins.**
- **CAN pairs** (2–3 channels of H/L, routable).
- **General I/O pins** (many): each routable to a wake/enable digital out, an analog sense
  tap, or a programmable load — via the matrix.

### Switch matrix (custom PCB, "Phase C")
A relay/FET crosspoint routing any station resource to any header pin under software control:
- **Mechanical relays for power/high-current paths** (cheap, low on-resistance, isolation).
- **Analog muxes/FETs for signal/sense paths** (fast, precise).
- Organized as **banks** — a full N×M crosspoint is rarely needed.
- Driven by an **RP2040/STM32** over USB serial (the `hal/matrix.py` target).
- **Hardware e-stop wired as an interlock** that cuts power rails independent of the MCU
  *and* the host.

### Protection & sensing
TVS + reverse-polarity + fusing on the DUT rail (non-negotiable, §10). **INA228 current
sense per power rail**; an ADC bank for analog taps. This is what makes per-state current
signatures first-class diagnostic data.

### Adapter-harness library (per-module, cheap) — with identity
The only per-module part: maps a module connector → standard header. Natural home for
**PDP-Connect** as the keyed station-side standard. **Every harness gets an identity**
(1-Wire EEPROM, ID resistor, or QR) so the station **auto-detects the attached harness and
loads the matching module profile** — closing the loop on "plug and run" and preventing
profile/harness mismatch.

### Honest constraint
A true "any resource to any pin" crosspoint that also carries 12 V @ 15 A *and* gives
mV-precision analog on the same pin is big and expensive. The win is **tiered pins + a
smart harness library**: universality without an absurd matrix.

---

## 4. Full-car simulator — a software-defined virtual vehicle

Restbus taken to its logical end: every module *not* on the bench becomes a controllable
virtual ECU, so when triaging an ECU you have live "controls" for engine, BCM, gateway,
ABS, etc. **All of it runs on `vcan` with zero hardware** — which is also what makes it a
shippable open-source "universal scanner" artifact.

### What it takes (in order of difficulty)
1. **DBC-driven periodic scheduler** (`cantools`) with correct cycle times — the easy 60%.
2. **Message integrity — the hard, essential 40%.** Modern modules reject frames lacking a
   valid **rolling alive-counter + per-message checksum / AUTOSAR E2E CRC** (VW, GM, …).
   The simulator must *compute* these per the platform's E2E profile or the DUT sits in
   fault. This is the thing cheap restbus tools get wrong.
3. **Network management** — AUTOSAR NM / OSEK NM keep-alive frames, ISO 11898-1 partial
   networking, UDS tester-present — so the DUT stays awake and out of limp mode.
4. **Virtual ECU "personalities"** — each absent module is a plugin that (a) broadcasts its
   frames and (b) **responds to UDS/diagnostic requests**, so a DUT (or a tech's external
   scan tool) sees a live network. This is "gateway-mode OBD" (§7.2) generalized.
5. **Closed-loop plant model** — when the DUT commands an actuator, feed back a plausible
   response (RPM rises, speed changes, sensors cohere) to clear *plausibility* DTCs, not
   just presence checks. Start with simple lookup/first-order models per platform.
6. **Multi-bus topology** — powertrain CAN, chassis CAN-FD, body CAN + a gateway that
   routes/translates between them (LIN/FlexRay/Ethernet later). Config-described like restbus.
7. **Fault injection as a first-class feature** — drop frames, corrupt CRCs, delay, stick
   signals, force bus-off, simulate shorted lines. Tests the DUT's fault handling **and**
   deliberately generates labeled symptom→cause data for the diagnosis corpus.

### Proposed package
Treat this as a first-class subsystem `canopy/sim/`, **not** just an internal restbus helper:
- `sim/vehicle.py` — orchestrates a set of virtual ECUs on one or more (v)CAN channels.
- `sim/ecu.py` — a virtual ECU: periodic TX + UDS responder + state.
- `sim/e2e.py` — alive-counter + checksum/CRC profiles (per-OEM plugins).
- `sim/nm.py` — network management.
- `sim/plant.py` — closed-loop plant models.
- `sim/faults.py` — fault injection.
- `vehicles/*.yaml` — per-platform vehicle definitions (which ECUs, which buses, which DBC).

---

## 5. Strategic view — why this is a game changer, and the moat

- **The simulator is the most reusable, most strategically valuable, and cleanly separable
  asset.** It doubles as the open-source "hosted OBD-II universal scanner": a
  software-defined vehicle bus anyone can plug a scan tool into for dev, training, and CI.
  Nothing good exists at that fidelity.
- **Data scarcity is the real constraint, not code.** DBCs, DID maps, E2E checksum
  algorithms, and **seed→key security access** are proprietary and per-OEM. Community
  efforts (opendbc/comma.ai) cover a slice. Broad coverage is the expensive part.
- **CBM is the perfect wedge.** Real modules + real techs labeling real `Case` records
  generate a symptom→cause dataset no open project has. That labeled corpus — not the
  simulator code — is the durable **moat**, and simultaneously the wiki. Build the capture
  loop (Phase 1 logging + Phase 5 cases) early so it compounds from day one.
- **Legal/safety framing**: diagnosis/repair and right-to-repair, *not* immobilizer/theft
  bypass. Keep confirm-before-energize and the hardware e-stop sacred.

### Sequencing tweak vs. the original roadmap
The Phase 0→6 order is right, but **pull a thin simulator slice into Phase 1**: DBC restbus
*with* alive-counter/CRC + NM, one platform, correct end-to-end — because it's pure
software, `vcan`-testable, required for real modules to talk, and the open-source crown
jewel. Get one platform *correct* before breadth.

---

## 6. Key decisions still open (resolve with Tom)
- Controller: Pi 5 vs. mini-PC.
- Production CAN interface: PEAK vs. Kvaser (multi-channel needs).
- Matrix channel count for Phase B; does PDP-Connect become the station-side header.
- Vision: Anthropic API (cloud) vs. local model (IP/data handling).
- J1939 scope in v1.
- **New:** first reference platform for the simulator (pick one with available DBC + known
  E2E profile to de-risk the hard 40%).
