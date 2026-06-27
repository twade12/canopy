# Output drivers and actuator circuits

> tags: output-driver, mosfet, high-side, low-side, h-bridge, relay, solenoid, motor, injector, flyback, dummy-load

Output stages fail because they handle real energy. A shorted actuator, inductive kick, stalled motor, wiring short, or wrong load can destroy a driver even if the logic side is healthy.

## Common output topologies
- **Low-side switch:** load tied to B+, MOSFET/driver pulls low.
- **High-side switch:** driver supplies B+ to load, often with current sense and diagnostics.
- **Half/H-bridge:** bidirectional motor or actuator control.
- **Relay driver:** transistor/MOSFET drives relay coil, with flyback suppression.
- **Solenoid/injector driver:** peak-and-hold or PWM current control, high flyback energy.
- **Triac/SSR:** appliance/industrial AC load control.

## Pre-repair checks
- Verify the downstream load is not shorted before replacing the driver.
- Measure output pin to ground/B+ for shorts.
- Diode-test MOSFET body diode and check drain-source short.
- Check gate resistor, gate pull-down, driver IC supply, bootstrap diode/cap for high-side stages, and flyback path.
- Inspect current-sense shunts and Kelvin connections.

## Dummy-load testing
- Use a current-limited dummy load matched to expected load type.
- Start with a resistor or lamp load before an inductive load.
- For solenoids/relays, include flyback handling or confirm the module contains it.
- Scope output voltage, current, and gate drive. A DMM cannot show flyback behavior or PWM current regulation.

## Smart high-side/low-side switches
- Many automotive smart switches include overcurrent, overtemperature, open-load detection, current sense, and fault reporting.
- A driver that shuts down under dummy load may be correctly protecting itself.
- Check diagnostic pins or SPI fault registers where accessible.
- Replacement must match current limit, protection behavior, package, thermal pad, and diagnostic interface, not just pinout.

## H-bridge and motor drivers
- Check for shorted high-side/low-side MOSFETs before applying power. Shoot-through can destroy the bridge instantly.
- Verify dead-time/gate-drive behavior if the gate driver is separate.
- Stalled motors draw far above running current. Use current-limited motor loads or electronic loads during bench validation.

## Failure clues
- Burned shunt or MOSFET: overcurrent or shorted load.
- Failed flyback diode/TVS: inductive transient or wrong clamp energy.
- Cracked solder on power package: thermal cycling/vibration.
- Repeated driver failure after replacement: downstream load or harness not fixed.

Sources: [Infineon automotive application guide](https://community.infineon.com/gfawx74859/attachments/gfawx74859/cnblogs/14418/4/Infineon-Automotive-Application-Guide-2016-ABR-v02_00-EN.pdf), [Infineon relay replacement in automotive power distribution](https://my.avnet.com/wcm/connect/af8106a7-15e2-4b1e-839f-9ae4ab593ea5/Infineon-Relay_replacement_within_automotive-ApplicationNotes-v01_00-EN%2B%281%29.pdf?MOD=AJPERES), [Infineon low-side switches](https://www.infineon.com/products/power/smart-power-switches/low-side-switches), [Nexperia driving automotive solenoids](https://www.nexperia.com/applications/interactive-app-notes/IAN50003_driving-automotive-solenoids), [Nexperia MOSFET EOS signatures](https://assets.nexperia.com/documents/application-note/AN11243.pdf).
