# Appliance and industrial board triage

> tags: appliance, industrial, mains, smps, relay, triac, optocoupler, plc, motor-drive, vfd

Appliance and industrial boards share many repair patterns with automotive modules, but they add mains hazards, isolation boundaries, relays/triacs, motor loads, environmental contamination, and sometimes 24 V control systems.

## Common appliance control board blocks
- Mains input fuse, MOV, NTC/inrush limiter, EMI filter, bridge rectifier, bulk capacitor.
- Offline SMPS with PWM controller, transformer, optocoupler feedback, TL431/reference, secondary rectifiers.
- Relay outputs for compressor, heater, pump, fan, valve, lamp, or lock.
- Triac outputs for AC motors, valves, heaters, or dimmed loads.
- Low-voltage MCU logic, display, buttons, thermistors, humidity/pressure/water-level sensors.

## Common industrial board blocks
- 24 VDC input protection and buck conversion.
- Digital inputs with optocouplers or resistor dividers.
- Relay/SSR/transistor outputs.
- 4–20 mA / 0–10 V analog inputs and outputs.
- RS-485, CAN, Ethernet, USB, isolated serial, encoder inputs.
- Motor-drive/VFD sections with rectifier, DC link, gate drivers, IGBTs/MOSFETs, and current sensing.

## Appliance faults
- Blown fuse + shorted MOV/bridge/MOSFET.
- Dried output electrolytic causing SMPS startup cycling.
- Open startup resistor starving PWM controller VCC.
- Relay contact pitting/welding causing stuck heater/pump/compressor output.
- Cracked solder on relays, transformers, power resistors, and connectors.
- Triac short causing load always on; optotriac/input failure causing load never on.

## Industrial faults
- Reverse polarity or surge damage on 24 V input.
- Shorted TVS on field wiring.
- Blown input resistor/opto from overvoltage.
- Relay contacts worn from inductive loads.
- RS-485 transceiver damaged by ground potential difference or surge.
- VFD power stage failure from shoot-through, failed gate driver, DC-link cap aging, or motor cable faults.

## Isolation rules
- Identify primary and secondary sides visually and with continuity.
- Do not connect grounded instruments across primary-side switching nodes without proper isolation/differential probing.
- Maintain creepage/clearance, slots, insulating sheets, and safety barriers after repair.
- Replace fuses, MOVs, X/Y capacitors, and safety parts with same safety class/rating.

Sources: [Rohde & Schwarz bench tools overview](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/dc-power-supplies/5-essential-tools-on-an-electronics-bench_256910.html), [Tektronix probe safety](https://www.tek.com/en/documents/whitepaper/abcs-probes-primer), [IPC Standards](https://www.electronics.org/ipc-standards), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf).
