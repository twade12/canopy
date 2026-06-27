# Standards and reference documents to keep in the knowledge base

> tags: standards, ipc, nasa, esd, jedec, aec, iso, sae, workmanship, reliability

A triage knowledge base should distinguish practical repair know-how from formal acceptance criteria. For paid repair, automotive, appliance, or industrial work, use standards as the guardrails and use this KB as the practical workflow layer.

## Workmanship, inspection, and repair standards
- **IPC-A-610 — Acceptability of Electronic Assemblies:** visual accept/reject criteria for finished assemblies. Use it when deciding whether a solder joint, component placement, lifted lead, contamination condition, or hardware condition is acceptable.
- **IPC J-STD-001 — Requirements for Soldered Electrical and Electronic Assemblies:** process requirements for creating soldered assemblies. Use it for soldering process discipline, flux/residue expectations, material control, and workmanship.
- **IPC-7711/7721 — Rework, Modification and Repair of Electronic Assemblies:** practical rework and repair procedures, including component replacement, trace/pad repair, coating removal, and board repair.
- **IPC-A-600 — Acceptability of Printed Boards:** useful when the fault may be the bare PCB: delamination, measling, annular ring defects, plating defects, voids, lifted pads, or via problems.
- **IPC/WHMA-A-620 — Cable and Wire Harness Assemblies:** useful for pigtails, bench harnesses, connector repairs, crimp quality, insulation damage, splices, and cable strain relief.
- **NASA-STD-8739.3 — Soldered Electrical Connections:** a strong visual/workmanship reference for high-reliability soldered connections.
- **NASA-STD-8739.1 — Polymeric Application on Electronic Assemblies:** useful for staking, bonding, conformal coating, and encapsulation decisions.

## ESD and handling
- **ANSI/ESD S20.20:** framework for an electrostatic discharge control program: training, grounding, personnel grounding, EPA setup, packaging, marking, and compliance verification.
- **JEDEC JESD625 / device-specific handling notes:** useful for semiconductor handling, packaging, and moisture-sensitive devices.

## Reflow and moisture sensitivity
- **IPC/JEDEC J-STD-020:** moisture/reflow sensitivity classification for non-hermetic SMD packages. Use it before reflowing ICs, BGAs, QFNs, and other moisture-sensitive packages.
- **Manufacturer solder profile:** always supersedes generic temperature guesses. Use the package-specific peak temperature, time above liquidus, ramp rate, and moisture sensitivity level.

## Automotive qualification and environment
- **AEC-Q100:** stress-test qualification for integrated circuits used in automotive applications.
- **AEC-Q101:** stress-test qualification for discrete semiconductors such as MOSFETs and diodes.
- **AEC-Q200:** stress-test qualification for passive parts such as resistors, capacitors, inductors, and thermistors.
- **ISO 16750 series:** environmental conditions and tests for electrical/electronic equipment mounted in or on road vehicles; covers electrical, mechanical, climatic, and chemical stresses depending on part.
- **ISO 7637 / ISO 16750-2:** relevant to automotive transients, load dump, reverse battery, cranking, and supply disturbance thinking.
- **ISO 11898:** CAN physical/data-link standards; use for formal CAN design and diagnosis references.
- **SAE J2716:** SENT sensor interface standard.

## Bench practice rule
- Use formal standards for acceptance and compliance; use datasheets for component limits; use this KB for repeatable fault isolation.

Sources: [IPC Standards](https://www.electronics.org/ipc-standards), [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [NASA-STD-8739.1](https://standards.nasa.gov/standard/NASA/NASA-STD-87391), [ANSI/ESD S20.20 overview](https://blog.ansi.org/ansi/ansi-esd-s20-20-2021-protection-electronic-parts/), [AEC Documents](https://www.aecouncil.com/AECDocuments.html), [ISO 16750 overview](https://www.iso.org/standard/69568.html), [IPC/JEDEC J-STD-020](https://shop.electronics.org/ipcjedec-j-std-020/ipcjedec-j-std-020-standard-only?f%5B0%5D=language%3A37), [SAE J2716](https://www.sae.org/standards/j2716-sent-single-edge-nibble-transmission-automotive-applications).
