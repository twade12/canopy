# Real bench instruments over USB (pyvisa / SCPI)

Canopy can drive a real bench **DMM** or **USB oscilloscope** over SCPI using `pyvisa`
(`canopy/hal/visa.py`). Pick the instrument in any panel's **Source** dropdown → it swaps the
simulator for the real device, and the same DMM/Scope panels read live measurements. Readings and
scope captures **record into the open project** and appear in its **Wiki** for audit/repair docs.

## Verified-compatible instruments (buy)

### Bench DMMs (5½/6½ digit, USB-TMC + SCPI)
| Model | Notes | Buy |
|---|---|---|
| **Rigol DM3058E** | 5½ digit, USB/RS232, great value | [amazon](https://www.amazon.com/Rigol-DM3058E-Digital-Multimeter/dp/B00KBZK1QW) |
| **Rigol DM3068** | 6½ digit, more precision | [amazon](https://www.amazon.com/Rigol-DM3068-Benchtop-Digital-Multimeter/dp/B00E3SM4BS) |
| **Siglent SDM3045X** | 4½ digit, fast, affordable | [amazon](https://www.amazon.com/Siglent-Technologies-SDM3045X-Digital-Multimeter/dp/B01IXPKIV4) |
| **Siglent SDM3055** | 5½ digit dual-display | [amazon](https://www.amazon.com/Siglent-Technologies-SDM3055-Digital-Multimeter/dp/B00QT3RTV0) |
| Keysight 34461A | 6½ digit, premium | (vendor/distributor) |

These all answer standard SCPI `MEAS:VOLT:DC?` / `:VOLT:AC?` / `:CURR:DC?` / `:RES?` / `:FREQ?`,
which is exactly what `VisaInstrument.dmm()` sends — so **measuring a battery** (leads on ±, mode
VDC) or **a resistor** (leads across it, mode Ω) just works.

### USB oscilloscopes (SCPI waveform read)
| Model | Notes | Buy |
|---|---|---|
| **Rigol DS1054Z** | 50 MHz, 4-ch, 1 GSa/s — the classic, best-documented | [amazon](https://www.amazon.com/Rigol-DS1054Z-Digital-Oscilloscopes-Bandwidth/dp/B012938E76) |
| **Rigol DS1104Z-S Plus** | 100 MHz, 4-ch + built-in 2-ch AWG | [amazon](https://www.amazon.com/DS1104Z-Oscilloscope-Channels-30000wfms-Decoding/dp/B08JGZ218X) |
| **Siglent SDS1104X-E** | 100 MHz, 4-ch, excellent SCPI | [amazon](https://www.amazon.com/Siglent-SDS1104X-oscilloscope-channels-standard/dp/B0922HKY44) |

`VisaInstrument.scope_frame()` implements the Rigol **DS1000Z** / Siglent **SDS1000X-E** waveform
read (`:WAV:SOUR/MODE/FORM`, `:WAV:PRE?` for scaling, `:WAV:DATA?` binary block) and pushes the
panel's trigger level/edge/coupling to the scope (`:TRIG:EDGE:*`, `:CHANx:COUP`). The DS1104Z-S's
built-in AWG also makes the **Signal Generator** panel meaningful on one box.

> Tip: a DS1054Z (scope) + a DM3058E (DMM) is a great, affordable pair that covers everything these
> panels do. The DS1104Z-S adds a real signal generator.

## Install the driver
Pure-Python backend (no NI-VISA needed):
```bash
pip install ".[visa]"      # pyvisa + pyvisa-py + pyusb + pyserial
```
**Linux USB-TMC permissions** — add a udev rule so you don't need root (example for Rigol VID
`1ab1`; use your device's VID via `lsusb`):
```
# /etc/udev/rules.d/60-usbtmc.rules
SUBSYSTEM=="usb", ATTRS{idVendor}=="1ab1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usbtmc", MODE="0666", GROUP="plugdev"
```
Then `sudo udevadm control --reload-rules && sudo udevadm trigger`, replug the instrument, and add
your user to `plugdev`. (Siglent VID is `f4ec`.)

## Connect + record in Canopy
1. Plug the instrument in over USB. In any instrument panel open the **Source** dropdown — VISA
   resources (e.g. `USB0::0x1AB1::0x0588::DM3R…::INSTR`) and serial ports are listed; pick yours.
   (Canopy auto-detects: a string with `::` / `USB`/`TCPIP`/`GPIB` → VISA, else a serial port.)
2. The badge flips to **LIVE** and the panel shows the instrument's `*IDN?`. Readings are now real.
3. **Record:** with a **project selected**, click **Record reading** (DMM) or **Capture** (Scope).
   Each is stored in the project — DMM readings as a value/unit row, scope captures as a PNG
   attachment — timestamped, deletable, and **compiled into the project Wiki** under *Recorded
   measurements* for the repair documentation.

## Endpoints (for automation)
`GET /api/instr/visa` (list resources) · `POST /api/instr/connect {source}` ·
`GET /api/instr/dmm?mode=` · `GET /api/instr/scope/stream` ·
`GET/POST /api/vehicles/{id}/measurement[s]` · `DELETE /api/measurement/{id}`.

## Safety
Respect the instrument's input ratings and use proper probes/leads. A bench DMM measuring a 12 V
battery or a resistor is routine; never exceed CAT/voltage ratings, and keep the DUT's grounds in
mind when it's also tied to CAB or a vehicle.
