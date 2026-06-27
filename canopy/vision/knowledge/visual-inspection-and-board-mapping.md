# Visual inspection and board mapping

> tags: visual-inspection, microscope, board-mapping, component-id, connector, reverse-engineering, block-diagram

Visual inspection is not “looking around.” It is a structured attempt to map board function, find physical evidence, and decide which block should be tested first.

## Photograph before touching
- Photograph both sides at high resolution before cleaning, rework, or component removal.
- Capture connector faces, pin numbering clues, markings, shields, thermal pads, coating, potting, burns, corrosion, and previous rework.
- Add an orientation mark in every photo so later notes do not confuse top/bottom or connector side.

## First-pass damage scan
- Look for water lines, green/white corrosion, soot, cracked packages, bulged electrolytics, discolored resistors, lifted pads, missing parts, cracked MLCCs, cracked solder around heavy pins, and overheated connector cavities.
- Inspect under conformal coating for darkened copper, dendrites, moisture trails, and cloudy coating.
- On automotive modules, inspect connector pins and perimeter seals before assuming internal component failure.

## Build a functional block map
- Draw the connector at the edge of the page and label known pins: B+, ignition/wake, grounds, CAN/LIN/K-line, sensor refs, inputs, outputs, and case/shield.
- Identify the input protection block: fuse, TVS, reverse-protection diode/FET, common-mode choke, bulk cap, and first regulator.
- Identify the logic block: MCU, clock/crystal/resonator, reset supervisor, EEPROM/Flash, debug pads, oscillator load caps, and local decoupling.
- Identify input and output blocks: op amps, resistor arrays, clamp diodes, current shunts, smart switches, MOSFETs, relay drivers, H-bridges, and gate-driver ICs.

## Component marking workflow
- Read top marks under angled light; photograph before cleaning if the marking is faint.
- Search exact package + top code + board context. A three-character code alone is not enough; use package, pin count, nearby passives, and connected nets.
- Determine whether the IC is power, transceiver, EEPROM, driver, op amp, sensor interface, or MCU by pins and surrounding parts.

## Net tracing workflow
- Start from connector pins and trace inward to the first component.
- Use continuity only on unpowered boards.
- Use diode mode to compare symmetric channels; a bad channel often reads different from adjacent known-good channels.
- Create a partial schematic for the suspect block only. You rarely need a full schematic to fix a board.

## Inspection red flags by location
- **Connector edge:** cracked joints, galvanic corrosion, fretting, burned pins, bent pins, broken solder anchors.
- **Power input:** open fuse, shorted TVS, cracked input cap, burned reverse FET, overheated shunt.
- **Regulator area:** cooked inductor, dry joints, cracked feedback resistors, hot LDO, ripple-stressed caps.
- **MCU area:** no clock, reset held low, contaminated oscillator, missing pull-up, shorted decoupler.
- **Output stage:** cracked power packages, failed flyback diode, shorted MOSFET, burnt current sense, lifted high-current pads.

Sources: [IPC-A-610 training description](https://stiusa.com/product/ipc-a-610-certified-ipc-trainer-cit-certification-program-lecture-based/), [IPC-A-600 overview](https://www.electronics.org/ipc-certifications), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [ChangeChip PCB defect detection paper](https://arxiv.org/abs/2109.05746).
