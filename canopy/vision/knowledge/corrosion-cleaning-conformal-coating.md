# Corrosion, cleaning, conformal coating, and potting

> tags: corrosion, water-damage, cleaning, flux, conformal-coating, potting, dendrites, leakage

Corrosion creates both opens and unintended resistors. It can make a board pass cold/dry and fail warm/humid. Cleaning must remove conductive residue without damaging coatings, labels, plastics, sensors, or calibration structures.

## Visual corrosion clues
- Green copper salts, white residue, blackened copper, cloudy coating, lifted solder mask, waterline marks, dendrites between pins, and stained connector cavities.
- Corrosion under ICs and connectors is often worse than what is visible on top.
- Fine-pitch MCU, EEPROM, oscillator, CAN transceiver, and sensor input areas are high-risk because leakage can change logic or analog thresholds.

## Failure mechanisms
- Copper trace opens.
- Leakage between adjacent pins or high-impedance nodes.
- Dendritic growth under bias.
- Corroded connector pins causing voltage drop under load.
- Corroded vias causing intermittent opens.
- Flux residue absorbing moisture and creating leakage/corrosion.

## Cleaning approach
- Photograph before cleaning.
- Remove loose contamination dry first when possible.
- Use appropriate cleaner for the residue and coating type; IPA alone may not remove all ionic contamination.
- Avoid soaking parts that trap fluid: relays, buzzers, displays, unsealed transformers, switches, MEMS sensors, and some connectors.
- Dry thoroughly before power. Trapped solvent/water can create a new fault.

## Conformal coating handling
- Identify coating type if possible: acrylic, silicone, urethane, epoxy, parylene.
- Acrylic is often easiest to remove chemically; silicone may require mechanical/chemical methods; epoxy/parylene can be difficult.
- Remove only the area needed for diagnosis/repair, then restore coating after verification.
- Keep coating away from connector contacts, test pads that must remain accessible, heatsink interfaces, and adjustable parts unless specified.

## Potting limits
- Potted modules may be uneconomical or destructive to open.
- Chemical or thermal dep ot ting can damage parts and erase evidence.
- For potted boards, external pin diagnosis, X-ray, current signature, thermal imaging, and known-good comparison are especially valuable.

## Repair verification for water damage
- Verify leakage-sensitive circuits under humidity/heat if possible.
- Check connector voltage drop under load.
- Recoat repaired areas and restore seals/gaskets.
- If corrosion reached the MCU/EEPROM/connector pins deeply, warn that long-term reliability may be lower even after apparent repair.

Sources: [NASA-STD-8739.1](https://standards.nasa.gov/standard/NASA/NASA-STD-87391), [NASA-STD-8739.1 PDF](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/nasa-std-8739.1b.pdf), [IPC cleanliness study](https://www.electronics.org/system/files/technical_resource/E2%26S25_03.pdf), [No-clean flux residue discussion](https://piektraining.com/en/no-clean-flux-residue-should-we-clean-it-or-not/), [IPC Standards](https://www.electronics.org/ipc-standards).
