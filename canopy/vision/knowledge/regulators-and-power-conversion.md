# Regulators and power conversion diagnosis

> tags: regulator, ldo, buck, boost, smps, flyback, ripple, feedback, enable, power-good

Regulators are the bridge between raw power and logic. A module with “good 12 V” can still be dead if the regulator input, enable, feedback, soft-start, clock, or output capacitor is wrong.

## Identify the regulator type
- **LDO:** input, output, ground, enable, sometimes adjust/feedback. Simple, low noise, heat-sensitive.
- **Buck converter:** controller/regulator IC, inductor, catch diode or synchronous FET, feedback divider, compensation network, output caps.
- **Boost/inverting converter:** inductor/diode/FET topology, often for displays, sensors, gate drive, VFD, or analog rails.
- **Flyback/offline SMPS:** transformer, primary switch, optocoupler feedback, startup resistor, auxiliary winding, isolation boundary.

## Regulator check sequence
- Verify input voltage at the IC pin, not just at the connector.
- Verify enable/wake pin state.
- Verify output voltage and ripple with a scope.
- Verify feedback pin near its reference voltage if accessible.
- Verify power-good/reset output if it gates the MCU.
- Check temperature. A regulator in thermal shutdown may pulse or restart.

## Buck converter faults
- Shorted output cap or load pulls rail low.
- Open/high-ESR output cap creates ripple, reset loops, or unstable regulation.
- Cracked inductor joint creates intermittent no-power or squeal.
- Shorted synchronous FET or catch diode pulls input or output down.
- Open feedback resistor can drive output high or prevent startup.
- Bad compensation or wrong replacement cap ESR can cause oscillation.

## LDO faults
- Input present, enable high, output zero: LDO failed, load short, thermal shutdown, or wrong pinout replacement.
- Output low with high current: downstream short or overloaded rail.
- Output unstable: output capacitor ESR/capacitance mismatch, bad ground, or marginal input.
- LDO runs hot: excessive input-output drop, overloaded output, wrong package thermal path, or shorted load.

## Offline/appliance SMPS faults
- Check fuse, MOV, NTC, bridge rectifier, bulk cap, primary MOSFET, startup resistor, PWM IC VCC, optocoupler, TL431/reference, secondary rectifiers, and output caps.
- If the supply ticks/cycles, suspect overload, bad startup supply, shorted secondary diode/cap, failed feedback, or primary current limit.
- Respect isolation. Primary ground and secondary ground are not the same.

## Repair verification
- Scope ripple at no load and expected load.
- Test startup with current limit and then with normal supply.
- Heat/freeze suspect regulator area for intermittent shutdowns.
- Confirm downstream MCU reset releases only after rails stabilize.

Sources: [Microchip power-up troubleshooting](https://ww1.microchip.com/downloads/en/Appnotes/00000607C.pdf), [TI automotive reverse polarity reference design](https://www.ti.com/lit/ug/tiduc42/tiduc42.pdf), [Rohde & Schwarz oscilloscope probe tips](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/rs-essentials-digital-oscilloscopes/oscilloscope-probe-tips-and-how-to-use-them_257202.html), [Keysight oscilloscope probing](https://prc.keysight.com/Content/PDF_Files/5989-7894EN.pdf).
