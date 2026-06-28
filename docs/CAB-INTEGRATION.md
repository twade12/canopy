# CAB ↔ Canopy integration — the north star

**CAB (Car-in-a-Box)** is a 10-slot modular benchtop HIL rig that safely powers a module under
test, emulates the missing vehicle, and measures behavior. **Canopy** is the brain: vision
onboarding (wiring diagram → pinout, board photo → components), grounded triage, the guided
walkthrough, the knowledge base, memories, and the wiki. This doc is the durable plan for joining
them. (See also: the CAB hardware reference PDF, `docs/CAB-PROTOCOL.md`, `docs/QUICKSTART.md`.)

## The one idea: Canopy is the brain, CAB is the body — the seam is the Module Profile
Canopy already is ~most of CAB's host-software brief (FastAPI + SocketCAN + python-can + cantools +
ISO-TP + udsoncan + SQLite/Postgres + YAML profiles + reports). The artifact that turns
"Canopy + a CAN adapter" into "Canopy + CAB" is the **Module Profile** (`canopy/profiles/`,
the Profile tab): identity, the pinout with each pin's **role**, the **harness map**
(module pin → CAB standard header → CAB card+channel), power/diagnostic settings, restbus/loads,
and safety gates. **Canopy auto-drafts it from the diagram/PCB; a tech confirms it; CAB executes
it.** Make that the center of gravity.

Onboarding any new module becomes: **wiring diagram → Canopy → confirmed profile + harness build
sheet → plug into CAB's universal header → triage.**

## Roadmap (tiers map onto the CAB phases)

### Tier 1 — software-only, validate on `vcan0` (no CAB hardware yet)
1. **Module Profile system** — *done* (`canopy/profiles/`, Profile tab). Next: enrich `signals`/
   `expected` from module-class templates + the KB.
2. **Harness / "universal plug" map** — *drafted by the profile generator*. Next: render a printable
   harness build sheet + the confirm-before-energize checklist.
3. **Restbus simulator** (`canopy/restbus/`): cantools DBC → periodic frames (gateway/ignition/NM)
   driven by the profile so the DUT leaves limp/sleep. Test on `vcan0`.
4. **DTC/UDS panel** tied to the profile + KB: read/clear DTCs (0x19/0x14), RDBI (0x22), DBC-decode,
   feed decoded DTCs into Guided/Triage as grounded evidence.
5. **Live bus monitor + DBC decode** in the Bench tab.

### Tier 2 — the CAB HAL (when first cards exist; CAB Phase 2)
6. **Host↔CAB serial protocol** — *done* (`docs/CAB-PROTOCOL.md`, `canopy/hal/cab.py` + mock).
   Next: a per-card-type helper layer + a `/api/cab/*` surface and a bench slot view.
7. **Profile-driven Test Runner** (`canopy/runner/`): the automated counterpart to Guided — arms
   cards safe-by-default, applies `signals`/`loads`, measures (INA current, ADC), compares
   expected-vs-observed, logs every energize, emits pass/fail + the wiki.
8. **Power & current first-class**: PSU + INA228 current signatures (inrush/quiescent/sleep) wired
   into the Guided "power-up" phase.

### Tier 3 — intelligence & scale
9. **Digi-Key / Mouser / Octopart APIs**: look up the part markings Canopy OCRs off the PCB →
   datasheet, lifecycle, stock/price, **substitutions**; auto-fill component specs; generate a
   **repair BOM per job**. Cache results so triage stays fast.
10. **Diagnosis engine** (`canopy/diagnosis/`): symptom-vector → ranked nearest past `Case`s
    (pgvector) + a rules YAML, surfaced in Guided/Triage as ranked root causes w/ confidence.
11. **Production workflow / queue**: quote intake → guided triage → (optional) automated CAB run →
    wiki + BOM + labor; multi-tech dashboard; a growing profile library keyed by make/model/year.

## UI direction
- A unified **Bench / CAB workspace** mirroring the front panel: a **10-slot visual** with live
  power/fault per card, the active profile, restbus controls, current/scope readouts, live CAN.
- **Let Guided drive the bench**: "apply 12 V current-limited" renders as a CAB `arm` with a confirm
  button and auto-records the measured current back into the log.
- Keep the **confirm-before-energize** modal as a hard gate wherever a profile would close a relay.

## Hardware / CAN-to-USB
- **Dev/MVP:** CANable 2.0 (gs_usb, CAN-FD, ~$50) on `vcan0` first. **Production:** PEAK PCAN-USB FD
  or Kvaser. **Multi-channel** for restbus-on-one-bus while talking to the DUT on another.
- **CAB link:** the backplane management MCU exposes one USB-CDC port; `canopy/hal/cab.py` speaks the
  v1 protocol. CAN to the DUT stays on the separate CANable/PEAK adapter.

## Safety (CAB §11 / CLAUDE §10) — always
Dummy-load-only for SRS/squib; current-limited bring-up; never connect a module to CAB and a live
vehicle simultaneously; sacrificial harness adapters; treat every OEM diagram as a hypothesis until
power/ground/CAN are verified; no destructive transients, HV EV, full EPS load, or flashing in v1.

## Highest-leverage next step
Tier 1 #3–#5 on `vcan0`: restbus + DTC/UDS panel + live decode. Pure software, immediately useful
with a $50 adapter, and it proves the profile→execution loop before a single CAB card is fabbed —
matching CAB's own "Phase 2: power + network bring-up" milestone.
