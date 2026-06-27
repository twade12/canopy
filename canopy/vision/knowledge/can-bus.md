# Tracing communication lines (CAN / LIN / K-line)

> tags: can, can-bus, lin, communication, comms, transceiver, termination, oscilloscope, network

When a module powers up but won't talk, work the physical layer before the protocol.

## CAN bus — resistance first (bus de-energized)
- Measure CAN-H to CAN-L with the bus powered OFF:
  - **~60 Ω** = healthy: two 120 Ω terminators in parallel, one at each end of the bus.
  - **~120 Ω** = one terminator missing / an open in the bus or a node disconnected.
  - **≤ ~40 Ω** = extra terminator or a short between the lines.
  - **0 Ω** = CAN-H shorted to CAN-L. **Open / very high** = broken bus wire.
- On a single module on the bench you are measuring that module's local termination (often 120 Ω,
  or none if it was a non-terminating node) — interpret relative to the module's design.

## CAN bus — voltages and signal quality (powered)
- Key on, engine off. CAN-H and CAN-L should idle (recessive) at **~2.5 V** each to ground.
- During traffic, **dominant** bits drive CAN-H up (~3.5 V) and CAN-L down (~1.5 V); differential
  ≥ 0.9 V = dominant, < 0.5 V = recessive. A line stuck high/low or biased far off 2.5 V points
  at the transceiver or its supply.
- A multimeter verifies termination, bias, and shorts but **cannot** judge signal integrity. When
  DC checks pass but comms are intermittent, scope CAN-H/CAN-L differentially: look for clean
  level transitions, correct bit timing, and absence of ringing/reflections (bad termination) or
  asymmetry (a weak/failing transceiver).

## Transceiver block checks
- Verify the transceiver's supply (often 5 V) and ground at the chip.
- Check the TXD/RXD lines between MCU and transceiver: TXD idles high; a TXD stuck low jams the
  bus (continuous dominant). RXD should follow bus activity.
- A transceiver that biases the bus wrong, won't ACK, or runs hot is a prime replacement
  candidate — confirm with the scope before swapping.

## LIN / K-line (single-wire)
- LIN idles near battery voltage through a pull-up (master ~1 kΩ, slave ~30 kΩ); recessive = high,
  dominant = pulled low. Check the pull-up and the LIN transceiver supply. K-line is similar
  single-wire, pulled to battery, scoped for the init/handshake.

Sources: [OBD-Cable – CAN bus health check (60/120/0 Ω)](https://obd-cable.com/can-bus-health-check-multimeter-resistance-diagnosis/),
[Pico – CAN bus physical layer test](https://www.picoauto.com/library/automotive-guided-tests/communication/can-bus/AGT-126-can-bus-physical-layer/),
[Kvaser – Testing CAN termination](https://kvaser.com/developer-blog/how-to-test-your-can-termination-works-correctly/).
