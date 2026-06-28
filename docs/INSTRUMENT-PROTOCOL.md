# Canopy bench instruments — serial protocol (v1)

Canopy's DMM / oscilloscope / signal-generator panels talk to a USB instrument over a simple
newline-delimited JSON serial link (same spirit as `docs/CAB-PROTOCOL.md`). A `MockInstrument`
ships in `canopy/hal/instruments.py` so all three panels are fully usable with **no hardware** — the
signal generator's output drives the simulated scope and DMM, so it's a self-consistent demo and a
drop-in once a real device is connected.

A suitable real device is any MCU (RP2040 / Teensy / STM32) that ADC-samples an input, drives a DAC
(or PWM/AD9833) output, and streams over USB-CDC.

## Transport
USB-CDC serial, 115200 8N1, newline-delimited compact JSON. Host sends a command object; the device
replies with one object. The scope uses a continuous stream.

## Commands (host → device)
| op | purpose | reply |
|---|---|---|
| `hello` | probe | `{fw, caps:["dmm","scope","siggen"]}` |
| `dmm` | one measurement | `{mode, value, unit, overload}` — `mode` ∈ `vdc vac adc aac resistance continuity frequency` |
| `siggen` | set the generator | echoes `{waveform, freq_hz, amp_vpp, offset_v, duty, enabled}` |
| `scope_start` | begin streaming frames | device emits `frame` lines until `scope_stop` |
| `scope_stop` | stop streaming | `{ok:true}` |
| `scope_cfg` | timebase/samples/trigger | `{ok:true}` |

## Scope frame (device → host, streamed)
```json
{"frame": 1, "dt": 2.0e-6, "ch1": [0.01, 0.42, ...], "trig": true}
```
`dt` = seconds between samples; `ch1` = volts. The host renders the graticule, V/div, and time/div.

## Signal generator parameters
`waveform` ∈ `sine square triangle sawtooth dc`; `freq_hz`, `amp_vpp` (peak-to-peak volts),
`offset_v`, `duty` (0–1, square only), `enabled`.

## Safety
Inputs are measurement-only and protected on the device; the generator output is low-voltage. The
host never drives loads through this path (that is CAB's job, `docs/CAB-PROTOCOL.md`).
