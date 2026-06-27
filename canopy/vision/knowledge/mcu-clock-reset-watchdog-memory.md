# MCU, clock, reset, watchdog, EEPROM, and Flash diagnosis

> tags: mcu, microcontroller, clock, reset, oscillator, watchdog, brown-out, eeprom, flash, boot

When rails are good but a module is dead, silent, or stuck in reset, move to the MCU support ecosystem. A “dead MCU” is often a missing clock, held reset, bad supervisor, bad power-good, corrupted EEPROM, or missing wake condition.

## MCU preconditions
- Correct core/I/O rails present and within tolerance.
- Reset line releases after rails stabilize.
- Clock oscillator runs or internal oscillator starts.
- Boot/config pins are not forced into programming/test mode.
- Watchdog/supervisor is not repeatedly resetting the device.
- EEPROM/Flash data needed for boot is readable and not corrupt.

## Reset line checks
- Scope reset during power-up. A DMM can miss repeated reset pulses.
- Reset held low: suspect supervisor, bad rail, pull-down fault, shorted cap, MCU internal fault, or external reset source.
- Reset oscillating: suspect rail ripple, brown-out threshold, watchdog, bad decoupling, or firmware crash.
- Reset high but no activity: check clock, boot pins, power-good dependencies, and MCU current draw.

## Clock checks
- Use a high-impedance probe and short ground. Probing a crystal directly can stop or distort oscillation.
- Check for cracked crystal/resonator, bad load capacitors, contamination near oscillator pins, missing series resistor, or MCU oscillator damage.
- Compare with a known-good board if waveform amplitude is unclear.
- No clock with good rails and released reset is strong evidence for oscillator network or MCU fault.

## EEPROM and Flash
- Do not erase, write, or “try programming” until you have made multiple read-only dumps where legally and contractually authorized.
- Compare dumps from repeated reads. Inconsistent reads indicate wiring, clip contact, power, or chip damage.
- Corrupt EEPROM can cause immobilizer, configuration, calibration, VIN, variant coding, adaptation, or learned-value faults.
- External EEPROM/Flash failure is less common than power/solder/cap faults, but data corruption is common enough to include in repeatable workflows.

## Boot and debug pads
- Identify debug/test pads but do not assume they are safe to use.
- Automotive MCUs may have locked debug interfaces, security states, or programming voltages that can brick devices if misused.
- Use read-only discovery first. Document pinout, voltage levels, and tool settings.

## Brown-out and watchdog reasoning
- Brown-out protection resets the MCU when supply voltage is below a threshold; repeated brown-out can look like firmware failure.
- Watchdogs intentionally reset the MCU when software stops servicing them. A watchdog reset is a symptom; find why software stopped.
- Always correlate reset behavior with rail ripple, enable state, and external loads.

Sources: [Microchip power-up troubleshooting](https://ww1.microchip.com/downloads/en/Appnotes/00000607C.pdf), [Microchip power supplies and brown-out](https://onlinedocs.microchip.com/oxy/GUID-D6FD9F43-8DC4-476E-A55E-AA21FA1CC865-en-US-4/GUID-7F9930D6-6D3C-43B9-ACA3-E596767C438C.html), [Infineon AURIX startup/reset](https://documentation.infineon.com/aurixtc3xx/docs/nyb1710229964455), [Renesas watchdog overview](https://renesas.github.io/fsp/group___w_d_t.html), [SiTime oscillator probing note](https://www.sitime.com/support/resource-library/application-notes/an10028-probing-oscillator-output).
