# CANOPY — Hardware: Schematics & BOM

> Companion to [ARCHITECTURE-NOTES.md](ARCHITECTURE-NOTES.md) and
> [BATTLE-PLAN.md](BATTLE-PLAN.md). This is the electrical design for the bench station
> **and** the modular "car-in-a-box" simulator. Board-level schematic intent + connector
> pinouts + BOM with real part numbers, scoped so a **one-week prototype** is buildable
> from off-the-shelf modules while the custom PCBs are in fab.

---

## 0. The one principle that drives every board

**The device under test (DUT) must not be able to tell the simulated car from a real one.**
That means the simulation has to be *electrically real at the connector*: real CAN
transceivers, real 12 V rails, real bus termination, real load on each pin — only the
*source of the data* is software. So the architecture puts a **fixed Standard Test Header**
between the DUT and everything else, and behind that header any section can be either a
**real vehicle harness** or a **simulator card** — the DUT sees identical electricals.

```
            ┌──────────────────────────── CANOPY station ────────────────────────────┐
   DUT ─────┤  Standard Test Header  ──►  Switch Matrix  ──►  { Power | CAN | Loads | │
 (e.g. F-250│   (fixed, keyed)            (route any            Measurement | SIM CARDS}│
  6.7L PCM) │        ▲                     resource→any pin)        │                   │
            │        │ adapter harness (per-module, auto-ID)        │                   │
            └────────┼──────────────────────────────────────────────┼──────────────────┘
                     │                                               │
              real module connector                      Host (Pi 5 / mini-PC) running
                                                         `canopy sim` → CAN adapters → bus
```

The simulator is just *another bank behind the matrix*. Pull the real-harness card, drop in
the sim card, and the same DUT now talks to a "whole car" that lives in software.

---

## 1. System as a card-cage (modular, hot-swappable sections)

Build it as a **backplane + plug-in cards** so any section is substitutable (this is the
literal "swap a PCB section for the real module" requirement). Cards share power, a control
bus (I²C/SPI/USB-serial), and the routed analog/CAN nets via the backplane.

| ID | Card | Role | Phase |
|----|------|------|-------|
| **M0** | Backplane + Standard Test Header | Fixed interface + inter-card routing | A |
| **M1** | Power & Protection | KL30/KL15 switching, reverse-polarity, e-fuse, per-rail current sense | A/B |
| **M2** | CAN / Bus Interface | Multi-segment transceivers, termination, fault-injection | A |
| **M3** | Switch Matrix | Relay/FET crosspoint: any resource → any header pin | B/C |
| **M4** | ECU Simulator card(s) | The "car in a box": MCU + transceivers presenting real buses; analog sensor/actuator emulation | B/C |
| **M5** | Signal Conditioning / Measurement | ADC banks, INA228 current, voltage dividers, protection | B |
| **M6** | Controller | Pi 5 / mini-PC + USB-CAN adapters (SocketCAN) | A |
| **M7** | Safety | Hardware e-stop + main contactor, independent of software | A |
| **H\*** | Adapter-harness library | Per-module connector → header, with identity chip | A→ |

---

## 2. M0 — Backplane & Standard Test Header

The fixed boundary the DUT mates to. **Tiered pins** (no pin is all things at once):

### Standard Test Header pinout (reference 40-pin; scale to 64 for big modules)
| Pins | Class | Net | Rating / notes |
|------|-------|-----|----------------|
| 1–4 | **Power** | KL30_SW (switched battery) | 12 V, e-fused, ≤20 A inrush, per-pin smart high-side switch |
| 5–6 | **Power** | KL15_SW (switched ignition) | 12 V, e-fused |
| 7–12 | **Ground** | GND | Star ground to PSU return + sense |
| 13–14 | **CAN-A** | CANA_H / CANA_L | Powertrain CAN/CAN-FD, 120 Ω switchable term |
| 15–16 | **CAN-B** | CANB_H / CANB_L | Chassis CAN-FD |
| 17–18 | **CAN-C** | CANC_H / CANC_L | Body CAN |
| 19–20 | **LIN** | LIN1 / LIN2 | Optional LIN (Phase later) |
| 21–36 | **GP-IO** | GPIO[0..15] | Each routable via matrix to: digital wake/enable out, analog sense in, or programmable load |
| 37–38 | **Reserved** | — | FlexRay/Ethernet/2nd power expansion |
| 39 | **ID** | HARNESS_ID (1-Wire) | Reads the attached harness's identity chip |
| 40 | **SHIELD** | CHASSIS | Cable shield / chassis bond |

Backplane carries: VBAT_RAW, KL30_SW, KL15_SW, GND (heavy copper), the three CAN segments,
a routed analog mux bus (16 lines), the control bus (I²C @ 3.3 V + SPI + USB-serial fan-out),
and the SAFETY_OK interlock line (must be high for any power relay to close).

---

## 3. M1 — Power & Protection

Protects cores and people (CLAUDE.md §10). One channel per switched rail.

**Signal chain (per switched rail, e.g. KL30_SW):**
```
VBAT_RAW ─► reverse-polarity FET ─► TVS clamp ─► smart high-side switch (current-limit+e-fuse)
         ─► INA228 shunt (current sense) ─► relay (SAFETY_OK gated) ─► header power pin
```
- **Source:** programmable bench PSU (Korad KA3005P / Riden RD6006) sets V + current-limit
  *before* energize, read back over USB. PSU is the "battery."
- **Reverse-polarity:** P-FET (e.g. Infineon **IPD90P04P4L** or a simple Schottky for low current).
- **Smart high-side switch / e-fuse:** Infineon **BTS7008-2EPA** PROFET (per-channel current
  limit, diagnostics) or **TPS1HB** family. This *is* the per-pin protection.
- **Current sense:** **INA228** (20-bit, ±, I²C) per rail — quiescent / sleep / inrush /
  per-state signatures. Highest-yield diagnostic data.
- **Relay:** automotive 12 V SPST (e.g. **Omron G5LE-1A** or a sealed mini-relay), coil driven
  by a low-side MOSFET **only if SAFETY_OK is asserted** (AND-gated in hardware).

---

## 4. M2 — CAN / Bus Interface

Presents *real* buses to the DUT so it can't tell sim from car.

- **Per segment (A/B/C):** a CAN-FD transceiver — **NXP TJA1051** (classic/FD) or **TJA1043**
  (partial-networking / bus-wakeup, better fidelity for sleep/wake tests). Each segment has a
  **software-switchable 120 Ω split termination** (relay or analog switch) so you can model
  termination faults.
- **To the host:** USB-CAN adapters on M6 hang off these same segments (the host's
  SocketCAN `can0/can1` *is* a node on the physical bus). Alternatively an on-card
  **MCP2518FD + MCP2562FD** gives the controller a native FD channel over SPI.
- **Fault injection (Track B3 in hardware):** relays/analog switches to (a) open CAN-H or
  CAN-L, (b) short H–L or either to GND/VBAT through a current-limited path, (c) inject
  series resistance. Drives real-world transceiver/termination fault signatures into the
  diagnosis corpus. **Strictly current-limited + SAFETY_OK gated.**

---

## 5. M3 — Switch Matrix (custom PCB, Phase C)

Routes any station resource to any header GP-IO pin.

- **Power/high-current paths:** mechanical relays (low Rds, isolation) — **Songle SRD** or
  **Omron G5LE** banks, driven through **ULN2803A** / dedicated low-side drivers.
- **Signal/sense paths:** analog crosspoint — **ADG1414** (SPI, daisy-chainable, 8×SPST) or
  **ADG715/ADG732** muxes — for ADC taps and low-current signals.
- **Controller:** **RP2040** (or STM32G0) over USB-serial implements `hal/matrix.py`; reads
  back relay states; holds all relays open unless SAFETY_OK.
- Organize as **banks**, not a full N×M crosspoint (cost/size). 16–32 channels for Phase B.

---

## 6. M4 — ECU Simulator cards (the "car in a box")

The substitutable section. Two flavors, mixed as needed:

**(a) Bus-side ECU emulation (digital).** The host runs `canopy sim run <vehicle>.yaml`;
one MCU+transceiver presents many virtual ECUs on one physical segment (alive-counters +
checksums + NM all computed in software — already working today). For higher channel counts
or hard-real-time timing, an **RP2040/STM32 + TJA1051** card can run a compiled restbus
locally and bridge to the host. Either way the DUT sees genuine differential CAN at correct
levels and cycle times.

**(b) Sensor/actuator emulation (analog).** Modules read more than CAN — they expect
sensors (VR/Hall crank/cam, NTC temps, pressure) and loads (injectors, solenoids, relays).
This card provides:
- **Programmable analog out:** DAC (**MCP4728**, 4-ch I²C) → buffer → divider for sensor
  emulation (temp, pressure, throttle position).
- **Frequency/pattern out:** MCU PWM/timer → level shift for crank/cam VR or Hall signals
  (so the PCM sees a "running engine").
- **Programmable loads:** power resistor + MOSFET banks to present realistic actuator
  impedance so driver-stage diagnostics and current draw look real.

This is exactly the substitution: unplug a real engine harness, plug in M4, the PCM still
sees crank pulses, coolant temp, and a live bus → it runs as if installed.

---

## 7. M5 — Signal Conditioning / Measurement

- **Voltage:** divider + RC filter + clamp → **ADS1115** (4-ch, I²C) or a LabJack T7 / MCC
  USB-DAQ for more channels / speed. Rail and GP-IO voltage capture.
- **Current:** INA228 banks (shared with M1) on each rail of interest.
- **Waveform (optional, high value):** SCPI scope (Rigol DS1000Z / Siglent SDS) via PyVISA
  taps CAN-H/CAN-L for differential integrity — ringing/asymmetry → failing transceiver/term.

---

## 8. M6 — Controller & CAN adapters

- **Host:** Raspberry Pi 5 (8 GB) + active cooler + NVMe (self-contained) **or** fanless
  x86 mini-PC (more headroom for DB + vision). Ubuntu 24.04 LTS, SocketCAN.
- **CAN adapters (SocketCAN, native):**
  - Dev: 2× **CANable 2.0** (gs_usb/candleLight, CAN-FD) → `can0`/`can1`.
  - Production: **PEAK PCAN-USB FD** or **Kvaser Leaf**; multi-channel **Kvaser USBcan Pro
    2xHS** for restbus-on-one-bus / DUT-on-another.
- The host bridges/gateways segments in software (or a sim ECU does), enabling multi-bus cars.

---

## 9. M7 — Safety (non-negotiable, build first)

- **Physical e-stop** (latching mushroom, e.g. **Schneider XB4/XB5**) in series with the
  coil of a **main contactor / power relay** that feeds VBAT_RAW to M1. Pressing it cuts DUT
  power **independent of the host and every MCU.**
- The same e-stop drives the **SAFETY_OK** backplane line low → all matrix/power relays open.
- Per-rail fusing (ATO blade fuses + holders) downstream of the PSU.
- Every energize/matrix event is logged in software for forensic traceability.

---

## 10. How modular substitution actually works (DUT sees no difference)

1. Tech plugs the module onto its **adapter harness**; the harness's **1-Wire ID chip**
   (**DS28E07** / **DS2431**) is read on header pin 39 → CANOPY auto-loads the matching
   module profile + vehicle sim config.
2. The matrix routes header power/ground/CAN per the profile (after the
   **confirm-before-energize** gate verifies power/ground pins).
3. Behind the header, the **sim bank (M4)** drives the CAN segments and analog pins — same
   transceivers, same 12 V, same termination a real car would present.
4. To the DUT, the electrical environment is indistinguishable from the vehicle. Swap M4 for
   a real-vehicle breakout and nothing on the DUT side changes.

---

## 11. Bill of Materials

### 11A — One-week prototype (off-the-shelf, no custom PCB)
Proves the full thesis: real module ← real CAN ← `canopy sim`, powered & current-sensed.

| Qty | Item | Example P/N | ~USD |
|-----|------|-------------|------|
| 1 | Raspberry Pi 5 8 GB + cooler + 27 W PSU + NVMe HAT/SSD | — | 160 |
| 2 | USB-CAN FD adapter (SocketCAN) | CANable 2.0 | 100 |
| 1 | Programmable bench PSU (USB control) | Korad KA3005P | 90 |
| 2 | High-side current monitor breakout | Adafruit **INA228** | 30 |
| 1 | CAN transceiver breakout (×3 for segments) | **TJA1051** / SN65HVD230 boards | 25 |
| 1 | 8-channel relay board (Pi HAT or USB) | Sequent **8-RELAY HAT** / Numato | 35 |
| 1 | Relay/matrix MCU | **RP2040** (Pico) | 5 |
| 1 | DAC for sensor emulation | **MCP4728** breakout | 10 |
| 1 | ADC for measurement | **ADS1115** breakout | 12 |
| 1 | E-stop + automotive contactor/relay | Schneider XB4 + 12 V contactor | 45 |
| — | Protection: TVS (**SMBJ28A**), ATO fuses+holders, P-FET, Schottky | assorted | 25 |
| — | Standard-header connectors, ID chips (**DS2431**), wiring, perfboard | assorted | 40 |
| 1 | Bench DMM (SCPI optional) | any | 60 |
| | **Prototype subtotal** | | **≈ $660** |

### 11B — Full station additions (custom PCBs + production instruments)
| Qty | Item | Example P/N | Notes |
|-----|------|-------------|-------|
| n | Smart high-side switches | Infineon **BTS7008-2EPA** PROFET | per power pin |
| n | Analog crosspoint switches | **ADG1414** (SPI) | matrix signal paths |
| n | Relays (power banks) | Omron **G5LE-1A** / Songle SRD | matrix power paths |
| 1 | Native FD controller (optional) | **MCP2518FD** + **MCP2562FD** | host SPI CAN |
| 1 | Partial-networking transceivers | NXP **TJA1043** | sleep/wake fidelity |
| 1 | Multi-channel pro CAN | **Kvaser USBcan Pro 2xHS** / PEAK PCAN-USB Pro FD | restbus + DUT |
| 1 | DAQ (more analog channels) | **LabJack T7** / MCC USB-DAQ | measurement |
| 1 | SCPI scope (waveform) | Rigol **DS1000Z** / Siglent SDS | CAN differential integrity |
| 4 | Custom PCBs (KiCad) | M0 backplane, M1 power, M2 bus, M3 matrix | fab @ JLCPCB/OSHPark |

---

## 12. KiCad project layout (when we spin boards)
```
hardware/
├── canopy-backplane/        # M0: header + routing + control bus + SAFETY_OK
├── canopy-power/            # M1: rails, reverse-polarity, PROFET e-fuse, INA228
├── canopy-bus/              # M2: TJA1051/1043 ×3, switchable term, fault-injection
├── canopy-matrix/           # M3: relay + ADG1414 crosspoint, RP2040
├── canopy-sim/              # M4: MCU + transceivers + DAC + load banks
├── canopy-measure/          # M5: ADS1115/dividers/clamps
└── lib/                     # shared symbols, footprints, the Standard Test Header
```
Each board is independently fab-able; the backplane is the only thing that must exist first.

---

## 13. One-week prototype plan (maps to BOM 11A)
- **Day 1–2:** Pi 5 + Ubuntu + 2× CANable as `can0`/`can1`; run `canopy sim run` on real CAN
  between the two adapters (no DUT yet) → confirm restbus + UDS over physical wire.
- **Day 2–3:** M7 safety first — e-stop + contactor + PSU current-limit. Then M1 single rail
  with INA228 logging via `hal/current.py` (mock → real).
- **Day 3–4:** TJA1051 segment on a breadboard; wire a **real reference module** (F-250 PCM)
  power/ground/CAN by hand; bring it up on the simulator's restbus → **module wakes**.
- **Day 4–5:** 8-relay board + RP2040 as a first `hal/matrix.py`; add the harness ID chip and
  auto-profile-load. MCP4728 + a crank-pattern output so the PCM sees a "running engine."
- **Day 5–7:** integrate: `canopy run <profile>` energizes safely, runs UDS, logs current +
  trace, writes a `TestRun`/`Case`. Capture one deliberately-injected fault signature.

> The entire software side (restbus, E2E, NM, UDS client/server, persistence) already runs
> on `vcan0` today — the prototype week is purely about putting real electrons behind it.
