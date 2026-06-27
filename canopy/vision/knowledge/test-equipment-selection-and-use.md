# Test equipment selection and use

> tags: test-equipment, dmm, oscilloscope, esr, lcr, thermal-camera, logic-analyzer, current-probe, bench-supply

A tool is useful only when its limits are understood. Most board triage uses a small set of instruments repeatedly: DMM, current-limited supply, oscilloscope, ESR/LCR meter, thermal camera, logic analyzer, and protocol interface.

## Digital multimeter
- Use DC voltage for rails, diode mode for junctions and TVS checks, resistance for de-energized nets, continuity for connector/net tracing, and min/max logging for intermittent drops.
- Confirm the board is de-energized before resistance, diode, or continuity tests.
- In-circuit resistance can lie because parallel paths exist. Lift one leg only when the result matters to the diagnosis.
- Diode mode is usually more useful than resistance for semiconductors because it shows forward voltage and reverse/open behavior.

## Current-limited bench power supply
- Set voltage and current limit before connecting the board.
- Watch the current signature: inrush then settle is normal; immediate current limit means short; near-zero current means open input path or no wake state.
- For shorts, inject a lower voltage into the affected rail, not full board voltage. Start low enough that the shorted device warms without burning traces.
- Record voltage, current limit, actual current, and which rails were active in every case note.

## Oscilloscope
- Use the scope when the value changes with time: switching ripple, reset pulses, clocks, CAN/LIN/SENT/PSI5 activity, MOSFET gate drive, injector/solenoid flyback, or intermittent drops.
- Use 10× probes for most work. Compensate probes before trusting waveform shape.
- Keep ground leads short. Long ground leads add inductance and can create false ringing, overshoot, or undershoot.
- Use differential probes or isolated instruments for non-ground-referenced measurements, mains, half-bridges, and motor-drive nodes.

## ESR/LCR meter
- ESR meters quickly find aged electrolytics, but compare against expected values for capacitance, voltage rating, package, and temperature class.
- LCR meters identify wrong-value passives, cracked MLCCs, bad inductors, and suspect current shunts.
- A cap can measure acceptable capacitance but excessive ESR; scope ripple confirms whether it matters in the circuit.

## Thermal camera, freeze spray, and heat
- Thermal cameras are excellent for short localization and overloaded ICs, but emissivity and shiny metal can mislead. Compare both sides of the board.
- Freeze spray and controlled hot air help find temperature-sensitive cracks, marginal oscillators, regulators in thermal shutdown, and intermittent solder joints.
- Do not use uncontrolled heat on BGAs, plastic connectors, MEMS sensors, electrolytics, or batteries.

## Logic analyzer and protocol tools
- Logic analyzers are useful for SPI/I2C/UART/SENT timing if the ground reference is safe and voltage levels match.
- For CAN/LIN, use both a physical-layer scope check and a protocol adapter. A protocol decoder cannot fix bad termination, bad common-mode voltage, or a damaged transceiver.
- For automotive modules on the bench, log power state, wake line, ignition state, termination, and traffic at the same time.

## Minimum bench stack
- DMM, current-limited supply, oscilloscope with appropriate probes, ESR/LCR meter, microscope, hot air + iron, soldering consumables, thermal camera or thermal indicator, CAN/LIN adapter, adjustable loads, and a documentation camera.

Sources: [Rohde & Schwarz bench tools overview](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/dc-power-supplies/5-essential-tools-on-an-electronics-bench_256910.html), [Fluke diode testing](https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-test-diodes), [Keysight Eight Hints for Better Scope Probing](https://prc.keysight.com/Content/PDF_Files/5989-7894EN.pdf), [Rohde & Schwarz oscilloscope probe tips](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/rs-essentials-digital-oscilloscopes/oscilloscope-probe-tips-and-how-to-use-them_257202.html), [ACDi thermal camera short localization](https://www.acdi.com/troubleshooting-electronic-board-power-rail-shorts-with-a-thermal-camera/).
