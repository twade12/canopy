# Tracing sensor lines (reference, signal, return)

> tags: sensor, 5v-reference, vref, signal, return, ground, analog, input, pull-up, short-to-ground

Most engine/chassis sensors are 2-wire (5 V reference + signal return) or 3-wire (5 V reference,
signal, and a dedicated ground). The module supplies and protects the reference and reads the
signal against its analog ground.

## Normal values
- **5 V reference:** 4.9–5.1 V at the sensor connector. 4.6 V or other out-of-range values =
  a partial short / high-resistance fault on the reference bus.
- **Sensor / signal ground:** essentially 0 V — a good ground shows **no more than ~0.01 V** of
  offset; more than ~0.1 V drop under load is a ground-side problem.
- **Signal:** within the manufacturer's range for the sensor's state (e.g. TPS sweeps smoothly).

## The unplug test — isolate sensor vs wiring vs module
With the reference low/missing/unstable, **disconnect the sensor** and re-measure the reference at
the harness (module side):
- **Reference returns to 4.9–5.1 V unplugged** → the sensor is internally shorted; replace it.
- **Reference stays low/absent unplugged** → fault is upstream: a short on the reference wire, a
  shared splice dragging the bus down (one shorted sensor can pull the whole 5 V ref bus), or a
  failed reference output in the module.

This one test separates a shorted sensor from a shorted wire or a module fault — do it before
condemning the board.

## Reasoning about the three lines
- Many modules share one 5 V reference across several sensors. A dead ref on multiple sensors at
  once points at the shared source/splice, not each sensor.
- On a 3-wire sensor, an **open sensor ground** drives the signal-return voltage high and can look
  like a signal fault — verify the sensor ground before chasing the signal.
- Inputs often have a pull-up/pull-down and clamp/filter (series R, cap to ground, protection
  diode). A signal stuck at rail or at ground can be the input network or protection, not the
  sensor — check the conditioning components at the module's input pin.

## On the board
- Trace the connector's reference/signal/return pins to the first components: the reference often
  comes from a protected regulator output; the signal goes through a series resistor / RC filter
  / clamp diodes into an ADC pin. Inspect those for cracked joints, cooked resistors, or a leaky
  clamp diode that loads the line.

Sources: [AutoSuccess – Understanding 5 V reference signals](https://www.autosuccessonline.com/understanding-5-volt-reference-signals/),
[autodtcs – Test a 5 V reference circuit](https://autodtcs.com/how-to-test-a-5v-reference-circuit-in-automotive-sensors-diagnose-low-missing-5v-ref/),
[Clore Automotive – Troubleshooting 5 V reference circuits](https://cloreautomotive.com/troubleshooting-5v-reference-circuits/).
