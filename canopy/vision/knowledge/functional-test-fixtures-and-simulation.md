# Functional test fixtures and simulation for repaired modules

> tags: fixture, simulator, bench-test, dummy-load, can, lin, sensors, verification, product-development

A repair process becomes scalable when the bench can reproduce the complaint, exercise the suspect block, and log pass/fail results without the whole vehicle, appliance, or machine.

## Fixture goals
- Provide safe, known-good power and grounds.
- Simulate wake/ignition/enable lines.
- Provide required communication termination and traffic where needed.
- Simulate sensors and loads without risking customer hardware.
- Log current draw, rails, outputs, communication, and fault behavior.

## Basic automotive module fixture
- Current-limited 12–14 V supply with fuse and emergency stop.
- Ground-first harness with labeled connector pins.
- KL30/B+, KL15/ignition, wake, and reference rails switchable independently.
- CAN termination selectable: none, 120 Ω, 60 Ω equivalent network as appropriate.
- CAN/LIN adapter for traffic and logging.
- Dummy loads: resistors, lamps, relay coils, solenoids, electronic load, motor load simulator.
- Adjustable sensor sources: potentiometers, resistor decade box, voltage source, PWM/SENT generator where needed.

## Appliance/industrial fixture
- Isolated supply or safe low-voltage test where possible.
- Series bulb/current limiter for first mains tests when appropriate.
- 24 V industrial input with current limit.
- Relay/triac dummy loads matched to output type.
- Opto-isolated input simulators.
- 4–20 mA and 0–10 V simulators.
- RS-485/CAN/Ethernet test adapters.

## Test sequencing
- Pre-power resistance and polarity check.
- Power ground → B+ → ignition/wake → logic verification.
- Confirm rails, reset, clock, current signature.
- Exercise communication.
- Exercise inputs one at a time.
- Exercise outputs into dummy loads one at a time.
- Stress test: soak, thermal, and vibration/flex only after basic pass.

## Logging pass/fail
- Record module ID, revision, date, technician, test fixture version, power settings, loads, firmware/tool versions, and measured values.
- Store waveform screenshots for borderline or new failure modes.
- Use pass/fail thresholds, not prose-only observations.
- Link each failed test to a triage card and repair action.

## What generic scan tools cannot do alone
- They cannot prove a board-level rail is clean.
- They cannot isolate a shorted output driver without a safe load.
- They cannot tell whether no-comms is caused by power, reset, transceiver, bus termination, or software state.
- They cannot reproduce non-vehicle sensor/load states unless the fixture provides them.

Sources: [Vector CAN physical layer problems](https://cdn.vector.com/cms/content/know-how/_application-notes/AN-ANI-1-115_HS_Physical_Layer_Problems.pdf), [TI CAN debugging](https://www.ti.com/lit/pdf/slyt529), [TI CAN FD MCAN app note](https://www.ti.com/lit/pdf/slaaet4), [Rohde & Schwarz bench tools overview](https://www.rohde-schwarz.com/us/products/test-and-measurement/essentials-test-equipment/dc-power-supplies/5-essential-tools-on-an-electronics-bench_256910.html), [Pico CAN physical layer test](https://www.picoauto.com/library/automotive-guided-tests/communication/can-bus/AGT-126-can-bus-physical-layer/).
