# Fault-tree templates for unknown PCBs

> tags: fault-tree, symptoms, diagnosis, triage, no-power, no-comms, short, intermittent, output-dead

Use these templates to force repeatable triage. Each tree starts with the observable symptom and moves only after the precondition is proven.

## No power / no wake
- Confirm connector pinout and ground.
- Current-limited power: observe current.
- If near-zero current: open fuse, open reverse-protection path, missing wake/enable, bad connector, open trace.
- If current-limit trips: input short, TVS, reverse FET, cap, regulator, downstream rail short.
- If raw power present: check 5 V/3.3 V rails.
- If rails present: check reset, clock, MCU activity, power-good.
- Verify original wake condition, not just bench standby.

## Fuse pops / input short
- De-energize.
- Measure B+ to ground.
- Inspect input TVS/MOV, bridge, reverse FET, bulk cap, high-side switch.
- Current-inject at low voltage.
- Thermal/millivolt-drop localize.
- Remove suspect, re-check short, then replace and retest.

## No comms
- Prove power, ground, reset, clock.
- De-energized bus resistance: CAN-H to CAN-L or expected LIN/K-line pull-up.
- Powered bus bias: CAN recessive around mid-supply, LIN/K-line high, transceiver supply present.
- Scope waveform and logic TXD/RXD.
- Check transceiver heat and diode-mode readings.
- Only after physical layer passes, investigate protocol/software/wake/security.

## Sensor reference low/missing
- Measure 5 V reference and sensor ground.
- Unplug sensor/load and remeasure.
- If reference returns: external sensor/load short.
- If reference stays low: harness/shared ref/module-side short.
- Isolate shared branches.
- On board, trace ref regulator/protection and check clamp/filter parts.

## Output dead
- Check whether module commands the output.
- Check load and harness for short/open.
- Use dummy load.
- Verify driver supply, gate/input command, output pin, current sense, diagnostics.
- If driver is failed, confirm downstream fault before replacement.

## Intermittent
- Reproduce under controlled heat/freeze/flex/vibration.
- Monitor rail, reset, clock, comms, and symptom simultaneously.
- Localize area, then component/joint.
- Repair one item, then reproduce again.

## Water damage
- Photograph before cleaning.
- Identify affected blocks.
- Check connector pins, high-impedance analog/clock/reset/comms areas.
- Clean/dry appropriately.
- Check leakage/continuity and rail shorts before power.
- Recoat and warn about reliability risk if corrosion is deep.

Sources: [Accelerated Assemblies PCB troubleshooting](https://www.acceleratedassemblies.com/blog/pcb-troubleshooting-guide-for-engineers--from-fault-to-fix), [Aivon PCB power diagnosis](https://www.aivon.com/blog/pcb-knowledge/troubleshooting-pcb-power-issues-a-systematic-approach-to-diagnosis-and-repair/), [Vector CAN physical layer problems](https://cdn.vector.com/cms/content/know-how/_application-notes/AN-ANI-1-115_HS_Physical_Layer_Problems.pdf), [Pico CAN physical layer test](https://www.picoauto.com/library/automotive-guided-tests/communication/can-bus/AGT-126-can-bus-physical-layer/).
