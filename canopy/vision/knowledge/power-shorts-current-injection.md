# Power shorts and current injection

> tags: short-circuit, current-injection, voltage-drop, thermal-camera, rail-short, low-resistance, power

A rail short is found by controlled energy and comparative measurements, not by repeatedly applying full power. The goal is to locate the first abnormal heat or voltage drop while avoiding trace damage.

## Before injection
- Identify the shorted rail. Do not inject into an unknown net.
- Measure resistance from rail to ground with the board de-energized. Compare similar rails or known-good boards when possible.
- Disconnect external loads and harnesses. A shorted actuator can make a good module look bad.
- Check obvious short candidates first: TVS diode, reverse-protection FET, bulk cap, MLCCs near hot zones, transceiver, output driver, regulator, and decouplers near damaged ICs.

## Low-voltage current injection method
- Set supply voltage low: commonly 0.5–1.0 V for low-voltage logic rails, or enough to produce detectable heat without exceeding safe power.
- Set current limit low, then increase slowly while watching current and board temperature.
- Inject across the shorted rail and ground using short, thick leads.
- Scan both sides with a thermal camera or use high-proof IPA/flux evaporation carefully as a hotspot indicator.
- The first component to heat is often the short, but high-current copper paths and planes can spread heat. Confirm electrically before removal.

## Millivolt / microvolt voltage-drop method
- Inject current into the shorted rail at safe low voltage.
- Use a sensitive DMM to measure millivolt drops along the rail path.
- Voltage drop increases toward the short because current flows through copper resistance.
- This is especially useful when the board has large ground/power planes and the thermal image is ambiguous.

## Sectionalizing
- Lift one end of ferrite beads, zero-ohm links, inductors, or series resistors that feed sub-rails.
- Remove the regulator or lift its output inductor only when you have evidence the downstream rail is shorted.
- Cut traces only as a last resort; document the cut and repair it with proper wire/jumper and strain relief.

## Interpreting short signatures
- **Input rail short:** suspect TVS, reverse FET, input cap, bridge rectifier, MOV, or high-side switch.
- **5 V/3.3 V logic rail short:** suspect MLCC, MCU, transceiver, sensor-reference IC, EEPROM, or regulator output cap.
- **Output rail short:** suspect MOSFET, smart switch, flyback diode, load driver, or connector contamination.
- **Intermittent short:** suspect cracked MLCC, conductive contamination, solder bridge, metal debris, flexed connector, or moisture.

## Repair verification
- After removing the suspect part, re-measure rail-to-ground resistance before powering.
- Power the rail with current limit and confirm normal current draw.
- Replace with a part that matches voltage, capacitance/ESR, package, temperature, AEC grade when needed, and failure mode requirements.

Sources: [ACDi thermal camera short localization](https://www.acdi.com/troubleshooting-electronic-board-power-rail-shorts-with-a-thermal-camera/), [Thermal imaging for PCB repair](https://thermalmaster.com/blogs/blog/thermal-imaging-for-quick-and-easy-pcb-repairs-a-beginner-s-guide), [TI automotive reverse polarity reference design](https://www.ti.com/lit/ug/tiduc42/tiduc42.pdf), [Nexperia MOSFET EOS signatures](https://assets.nexperia.com/documents/application-note/AN11243.pdf).
