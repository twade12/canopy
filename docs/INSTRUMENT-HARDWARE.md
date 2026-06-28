# Putting the Canopy instruments on real hardware

Today the DMM / scope / signal-generator panels run against a built-in **simulator**
(`MockInstrument`). The panels are the *control surface*; the physical measuring is meant to be
done by a small **USB front-end** that streams readings to Canopy. Canopy already has the host side:
`SerialInstrument` in `canopy/hal/instruments.py` speaks `docs/INSTRUMENT-PROTOCOL.md` over a USB
serial port. So "make it real" = **attach a device that implements that protocol**, then pick its
port in the panel's **Source → Connect**.

```
  probe / leads ─► [ USB front-end: protection → conditioning → ADC/DAC → MCU ] ─USB-CDC─► Canopy
                        (this is the part you buy or build)                       (already done)
```

There are two paths. Most people want **Path A** for a Canopy-native, low-cost rig and **Path B**
when they need serious bandwidth.

---

## Path A — build/flash a low-cost MCU front-end (Canopy-native, recommended)

A single microcontroller that enumerates as a USB serial port and answers the v1 protocol
(`hello/dmm/siggen/scope_*`). This is the same philosophy as the CAB cards.

**Brains:** Raspberry Pi Pico (RP2040), Teensy 4.x, or an STM32 — all do USB-CDC. Teensy 4.x has the
fastest ADC/DMA; the Pico is the cheapest and Scoppy-class firmware shows ~500 kSa/s is achievable.

### Oscilloscope front-end (the analog front-end / "AFE" is the real work)
Your scope **probe** plugs into a **BNC jack** on the front-end, then:
1. **Protection:** series resistor + clamp diodes (e.g. BAV199) to the rails, so a stray 12 V (or a
   spike) can't kill the ADC. A PTC/fuse helps.
2. **Attenuation/range:** a 1×/10× divider (relay- or MOSFET-switched) so you can view ±0.1 V up to
   ±20 V+. A 10:1 scope probe extends this further.
3. **Bias/level-shift:** the ADC reads 0–3.3 V, but signals swing negative — an op-amp adds a
   mid-rail offset (a DAC sets it) so 0 V lands at mid-scale. This is also where **AC coupling** (a
   series cap) lives.
4. **Digitize:** the MCU's ADC (or an external fast ADC like the ADS7042 / MCP33131) sampled by DMA
   into a buffer, then streamed as `scope` frames.
5. **Trigger:** done in firmware — watch the sample stream for the level/edge Canopy sends via
   `scope_cfg` and align the buffer (Canopy's trigger dials map straight onto this).

**Reality check on bandwidth:** an MCU-ADC scope is ~tens of kHz to ~1 MSa/s. That's good for
automotive sensor signals, PWM/injector/relay drive, idle CAN-bus *levels*, and most board-level
work — but it will **not** resolve fast CAN edges cleanly or anything RF. For those, use Path B.

### DMM front-end
Standard **banana/probe leads** into the front-end, then per mode:
- **Voltage:** input protection + a precision divider into a good ADC (the MCU's, or an external
  ADS1115/MCP3421 for more resolution) against a precision reference (e.g. a 2.5 V LDO ref). This is
  how you measure a **battery** — black on −, red on +, read VDC.
- **Current:** a **shunt resistor** + a current-sense amp (INA240/INA226); report mA/A.
- **Resistance:** push a known current (or ratiometric vs a known reference resistor) and measure the
  drop → ohms. This is how you check a **resistor** — leads across it, read Ω.
- **Continuity:** threshold on the resistance reading (< ~50 Ω) + a buzzer; Canopy shows CONT/OPEN.

### Signal generator front-end
The MCU's DAC (or an **AD9833** DDS) into an output buffer/amp; Canopy's waveform/freq/amp/offset/
duty map directly to the `siggen` command.

### Minimal starter BOM (scope+DMM+siggen on one board)
| Block | Example parts |
|---|---|
| MCU + USB | RP2040 (Pico) or Teensy 4.0 |
| Scope protection | BAV199 clamp, 1 kΩ series, PTC |
| Scope range/bias | resistor divider + relay/MOSFET, MCP6L92 op-amp, MCP4725 DAC for offset |
| Fast ADC (optional) | ADS7042 / MCP33131 (else use MCU ADC) |
| DMM ADC + ref | ADS1115 / MCP3421 + REF3025 2.5 V |
| Current sense | INA240 + milliohm shunt |
| SigGen | AD9833 DDS + op-amp buffer (or MCU DAC) |
| Connectors | BNC (scope), banana jacks (DMM/leads) |

> **Don't want to design a PCB?** Wire it on a protoboard, or just stream the MCU's raw ADC for a
> first light — even a Pico reading its ADC into the `scope` protocol will draw a live trace in
> Canopy. The CAB project can also host these as bench cards later.

---

## Path B — buy an off-the-shelf USB instrument + add a driver

Off-the-shelf USB scopes/DMMs are far higher-bandwidth but **do not speak our serial protocol** —
each needs a small driver in `canopy/hal/instruments.py` (a sibling of `SerialInstrument`):

- **SCPI over USB (USBTMC) — the clean integration.** Many bench instruments expose SCPI over USB:
  scopes (Rigol DS1000Z, Siglent SDS800/1000), DMMs (Rigol DM3058/DM3068, Siglent SDM3045/3055),
  and AWGs. A **pyvisa**-based `VisaInstrument` would map our DMM/scope/siggen calls to SCPI
  (`MEAS:VOLT:DC?`, `:WAV:DATA?`, `SOUR:FUNC SIN`, …). This is the best "buy it and it just works"
  path for serious measurement and is a natural next feature.
- **PC USB scopes with vendor SDKs:** PicoScope (great SDK, 10s–100s MHz), Hantek 6022, OWON. These
  need a per-vendor driver (PicoScope's `picosdk` is the nicest). More work, highest performance.
- **Handheld DMMs with USB/serial out:** some (e.g. certain UNI-T/Owon) stream a fixed serial
  protocol; a tiny parser maps them in.

If you tell me which one you buy, I'll add the driver so the same Canopy panels drive it.

---

## How you actually connect it in Canopy
1. Plug the device in. On Linux it appears as `/dev/ttyACM0` (USB-CDC) or `/dev/ttyUSB0`.
2. Open **DMM / Scope / Signal Gen** → **Source** → pick the port → **Connect** (this swaps
   `MockInstrument` for `SerialInstrument`). Picking *Simulated* returns to the demo.
3. Probe your battery/resistor/signal — the panels now show real measurements; the dials, V/div,
   time/div, and trigger all command the device.

## Safety (do not skip)
Front-end **input protection on every probe input** (clamp + series R + fuse). Respect the front
end's voltage/current ratings — automotive 12 V/24 V is fine with proper dividers; **mains and HV
are dangerous** and out of scope for a hobby front-end. Isolation (an isolated USB or isolated ADC)
is strongly recommended when the DUT shares grounds with the vehicle or other tools.
