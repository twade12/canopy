# Component-level checks and repair

> tags: components, capacitor, esr, solder, reflow, diode, mosfet, resistor, in-circuit, rework

Practical, mostly in-circuit checks for the parts that actually fail, plus the repair action.

## Electrolytic capacitors (the #1 aged-board failure)
- Most common failure on boards roughly 1990s–2010s. Look for bulged tops, vented rubber, brown
  residue, or splayed legs.
- **ESR meter in-circuit:** a reading more than ~3–5× the datasheet ESR = bad cap. Rising ESR and
  lost capacitance cause ripple, rail sag, reset loops, and noise.
- Confirm with the scope: ripple on the rail it filters. **Repair:** replace with same or higher
  voltage, same capacitance, ≥ the original temperature/ESR rating; observe polarity.

## Solder joints (cold / cracked / fatigued)
- A cold or cracked joint is a weak/incomplete bond → intermittent, heat- or vibration-sensitive
  faults. Highest risk: connector pins, heatsink-mounted power devices, large/heavy parts, and
  anywhere with prior rework.
- Find them: magnification, gentle probe/flex while powered (intermittent appears), thermal.
- **Repair (reflow):** add flux, reflow with iron or hot air. Keep hot-air dwell under ~30 s per
  joint and shield neighboring parts (kapton/heat shield). Add fresh solder; inspect for a shiny
  concave fillet.

## Diodes (signal, rectifier, TVS, Zener)
- DMM diode mode in-circuit: ~0.15–0.45 V (Schottky) or ~0.5–0.7 V (silicon) forward, open
  reverse. **~0 V both directions = shorted; open both = blown.** A shorted protection/TVS or
  catch diode drags a rail and trips current limit — a fast find for "fuse pops / rail dead".

## Transistors / MOSFETs (output drivers, power stage)
- Output drivers fail from shorted actuators (solenoid/relay/motor) — the customer complaint
  often is the actuator, and it took the driver with it. Check the suspect output pin's driver.
- MOSFET in-circuit: diode-test the intrinsic body diode (S→D) and look for D–S shorted. A driver
  that's hot at idle or won't switch (verify gate drive with the scope) is suspect.
- **Repair:** replace the driver AND fix/confirm the downstream short first, or it fails again.

## Resistors / shunts / networks
- Cooked/discolored resistors signal an overcurrent event upstream — find the cause, don't just
  replace the resistor. Verify value in-circuit cautiously (parallel paths mislead); lift one end
  if it matters. Current-sense shunts read milliohms — verify continuity and look for cracks.

## Crystals / oscillators, EEPROM/Flash
- No clock = dead MCU symptoms with good rails: scope the crystal pins for oscillation; a cracked
  crystal or its loading caps stops it. EEPROM/Flash rarely fails open but can corrupt — note the
  part for data recovery/cloning workflows.

## Bench hygiene
- Temperature-controlled iron (fine tip), solder wick + flux, 99% IPA + ESD brush, DMM with
  continuity/diode, 10–30× loupe or microscope, ESR meter, and a current-limited bench PSU.

Sources: [LCSC – PCB refurbishing & repair guide](https://www.lcsc.com/blog/pcb-refurbishing-guide/),
[AllPCB – Cold solder joints, hot-air rework](https://www.allpcb.com/blog/pcb-manufacturing/troubleshooting-cold-solder-joints-hot-air-rework-to-the-rescue.html),
[PCBCool – Capacitor failure analysis](https://pcbcool.com/technical-guides/what-causes-a-capacitor-to-fail/).
