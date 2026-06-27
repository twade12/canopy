# Bench safety, ESD, and device-under-test protection

> tags: safety, esd, bench, isolation, current-limit, automotive, mains, dut-protection, oscilloscope

A repair bench can destroy the board, the instrument, or the technician if the DUT is energized before its power domain and hazards are understood. Safety is part of diagnosis, not an afterthought.

## Pre-power safety gate
- Identify the highest-energy input before energizing: vehicle battery B+, mains AC, DC bus, inverter bus, motor phase, supercapacitor, battery pack, or charged bulk capacitor.
- Assume bulk electrolytics and motor-drive DC-link capacitors remain charged until measured. Discharge through an appropriate resistor, not a screwdriver.
- Verify polarity and ground assignment from a pinout or board trace. Never energize unknown connector pins because a silkscreen label or wire color “looks right.”
- Start with a current-limited supply and a fuse. A current limit saves parts; a fuse protects wiring and the bench if the supply cannot respond fast enough.

## Oscilloscope ground hazard
- Most bench oscilloscopes have probe ground clips tied to protective earth through the power cord. Connecting a probe ground clip to a non-ground node can short that node to earth.
- Do not float a grounded scope by defeating the earth pin. Use a differential probe, isolated input scope, isolation transformer where appropriate, or battery-powered isolated measurement setup.
- Connect the probe to the scope first, connect ground safely, then probe the signal. Remove the signal tip before disconnecting ground.

## ESD discipline
- Use an ESD mat, wrist strap, grounded tools, and ESD-safe packaging for loose ICs and boards.
- Keep boards in ESD bags or conductive bins when not actively inspecting them.
- Avoid synthetic clothing, sliding plastic trays, Styrofoam, and loose vinyl around exposed MCUs, EEPROMs, sensors, RF modules, and MOSFET gates.
- ESD damage may not fail immediately. A board can pass today and become intermittent later.

## Automotive-specific safety
- Do not bench-fire pyrotechnic or SRS loads. Airbag/pretensioner circuits need manufacturer procedures, approved simulators, and strict authorization.
- Use dummy loads for relays, solenoids, lamps, motors, injectors, and clutches. Do not use a customer actuator until the driver stage is proven safe.
- For emissions, immobilizer, anti-theft, safety, brake, steering, and airbag systems, diagnose only in authorized repair contexts and do not bypass legally required protective functions.

## Appliance and industrial board safety
- Appliance control boards often contain non-isolated mains sections, capacitive droppers, triacs, MOVs, relays, and large capacitors. Treat “low-voltage” logic ground as potentially live until isolation is proven.
- Industrial boards may contain 24 V logic, 120/240 VAC input, VFD DC links, optocouplers, SSRs, and hazardous stored energy.
- Use isolation and differential probing when measuring across non-isolated power supplies or triac circuits.

## DUT protection rules
- Power ground first, then permanent B+, then switched/wake/ignition rails, then references and loads.
- Bring current limit up gradually. If current limit trips, stop and localize the short; do not repeatedly “try again.”
- Never replace a blown fuse with a higher rating during diagnosis. Use a current-limited supply, bulb limiter, or series resistor to observe behavior safely.
- After repair, restore protective coatings, shields, thermal pads, insulation barriers, and mounting hardware. Many “successful” repairs fail because the protection was not reassembled.

Sources: [Tektronix ABCs of Probes](https://www.tek.com/en/documents/whitepaper/abcs-probes-primer), [ANSI/ESD S20.20 overview](https://blog.ansi.org/ansi/ansi-esd-s20-20-2021-protection-electronic-parts/), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [Rohde & Schwarz bench tools overview](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/dc-power-supplies/5-essential-tools-on-an-electronics-bench_256910.html).
