# Thermal, vibration, and mechanical intermittent faults

> tags: intermittent, thermal, vibration, cracked-solder, connector, flex, freeze-spray, heat

Intermittent faults are evidence-sensitive. The goal is to reproduce the symptom safely, localize the sensitive area, and then confirm the exact joint, component, or connector before repair.

## Common intermittent causes
- Cracked solder on connectors, relays, transformers, heatsinked regulators, MOSFETs, large electrolytics, and inductors.
- Cracked MLCCs from board flex.
- Marginal oscillator or crystal that stops with temperature.
- Regulator entering thermal shutdown.
- Connector fretting/corrosion causing voltage drop under vibration.
- BGA/QFN solder fatigue.
- Broken via or inner-layer crack.

## Reproduction methods
- Flex board gently in controlled areas while powered and monitored.
- Tap/probe nonconductively around suspect zones.
- Apply freeze spray or controlled heat to small regions.
- Use min/max or scope triggering to catch rail drop/reset/comms loss.
- Monitor current draw, reset, clock, and communication at the same time.

## Do not over-stress
- Do not bend boards beyond normal mounting strain.
- Avoid heat on electrolytics, MEMS sensors, plastic connectors, batteries, displays, and adhesives.
- Freeze spray can create condensation; dry before further power testing.

## Localization strategy
- Start with connectors and heavy parts.
- Compare visual cracks under microscope with electrical symptoms.
- Use a continuity or resistance measurement while flexing only on de-energized boards.
- For BGA suspicion, check whether pressure/thermal changes alter behavior, but avoid blind reflow as first repair.

## Repair verification
- Reflow or replace the confirmed joint/component.
- Repeat the exact thermal/flex/vibration condition that reproduced the fault.
- Perform a short soak test under expected current and temperature.
- Restore mechanical support: screws, heatsinks, thermal pads, potting/staking, brackets, and strain relief.

Sources: [IPC-A-610 training description](https://stiusa.com/product/ipc-a-610-certified-ipc-trainer-cit-certification-program-lecture-based/), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf), [Thermal imaging for PCB repair](https://thermalmaster.com/blogs/blog/thermal-imaging-for-quick-and-easy-pcb-repairs-a-beginner-s-guide), [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english).
