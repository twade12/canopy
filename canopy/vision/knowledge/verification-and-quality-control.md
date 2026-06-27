# Repair verification and quality control

> tags: verification, quality-control, qc, burn-in, soak, pass-fail, repair-log, reliability

A replaced component is not a completed repair. A completed repair is a verified restoration of the original symptom with evidence that the board can survive expected use.

## Minimum verification record
- Original symptom.
- Initial measurements proving the fault.
- Root cause conclusion and confidence.
- Repair action and replacement part data.
- Post-repair measurements.
- Functional test result against the original complaint.
- Stress/soak result when applicable.

## Electrical checks after rework
- Rail-to-ground resistance before power.
- Current-limited startup current.
- Logic rail voltages and ripple.
- Reset and clock behavior.
- Communication physical layer.
- Suspect input/output function under dummy load or simulator.
- Thermal scan under operating load.

## Stress tests
- **Soak:** run for a defined duration at expected load.
- **Thermal:** controlled heat/freeze around repaired block for intermittent faults.
- **Vibration/flex:** only within realistic mechanical limits.
- **Power cycling:** repeated startup/shutdown catches marginal reset, boot, EEPROM, and inrush issues.
- **Load cycling:** output drivers, relays, solenoids, motors, and LEDs need switching tests.

## Acceptance criteria
- Use numeric thresholds whenever possible: voltage, ripple, current, temperature, communication error count, output current, resistance, response time.
- For visual acceptance, use IPC/NASA workmanship criteria as the reference layer.
- If a board passes only without its case/heatsink/thermal pad, it has not passed.

## Comeback prevention
- Fix the cause, not only the failed part. A shorted MOSFET may have been caused by a shorted actuator, missing flyback path, overheated solder joint, or corrosion.
- Replace aging companion parts when the failure mechanism affects a group, such as electrolytics in the same hot SMPS area.
- Update the case history so the next unit of the same type starts with the verified known pattern.

Sources: [IPC-A-610 training description](https://stiusa.com/product/ipc-a-610-certified-ipc-trainer-cit-certification-program-lecture-based/), [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [ISO 16750 overview](https://www.iso.org/standard/69568.html).
