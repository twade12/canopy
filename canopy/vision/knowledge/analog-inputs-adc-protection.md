# Analog inputs, ADCs, protection, and signal conditioning

> tags: analog, adc, input-protection, op-amp, sensor, 4-20ma, thermistor, rtd, shunt, filter

Analog inputs fail at the connector-facing protection network more often than at the MCU ADC pin. Trace the signal from the connector inward and prove reference, return, conditioning, and clamp behavior before condemning the ADC.

## Common analog input topology
- Connector pin.
- Series resistor or ferrite.
- ESD/TVS or clamp diodes to rails.
- RC low-pass filter.
- Divider, pull-up, pull-down, bridge, or bias network.
- Op amp/instrumentation amp/comparator/ADC input.
- MCU ADC or external ADC.

## What to check first
- Sensor reference voltage and sensor ground/return.
- Signal voltage at connector and at the first IC input.
- Series resistor continuity and value.
- Clamp diode leakage or short.
- Filter capacitor leakage or short.
- Op amp supply rails and output saturation.

## Symptom interpretation
- **Signal stuck at ground:** shorted sensor/wire, shorted filter cap, shorted clamp, dead op amp, or MCU input damage.
- **Signal stuck at reference/rail:** open ground/return, open divider leg, pull-up only, short to reference, or high-side leakage.
- **Noisy signal:** bad ground, failed filter cap, poor shield, reference ripple, op amp instability, or cracked solder.
- **Wrong but smooth signal:** wrong pull-up value, drifted resistor, sensor mismatch, calibration data issue, or ADC reference error.

## 4–20 mA and industrial analog loops
- A 4–20 mA input usually has a precision shunt resistor converting current to voltage.
- Check shunt value, solder cracks, input protection, loop supply, and common-mode range.
- A 0 mA reading can be open loop, blown shunt, open fuse/PTC, missing loop supply, or damaged input.
- A saturated high reading can be shorted transmitter, shorted protection, wrong burden resistor, or op amp saturation.

## Thermistors, RTDs, and bridge sensors
- Thermistors usually use a pull-up/pull-down divider. Check bias resistor and ADC reference.
- RTDs may use constant-current excitation; check current source and sense amplifier.
- Wheatstone bridge sensors require excitation, signal pair integrity, and instrumentation amplifier common-mode range.

## ADC reference faults
- If multiple unrelated analog channels are wrong by a similar ratio, suspect ADC reference, analog ground, or shared excitation.
- Scope ADC reference for ripple/noise; a DMM average can hide switching noise.
- Check reference decoupling and load.

Sources: [AutoSuccess 5 V reference overview](https://www.autosuccessonline.com/understanding-5-volt-reference-signals/), [Clore Automotive 5 V reference circuits](https://cloreautomotive.com/troubleshooting-5v-reference-circuits/), [Keysight probing note](https://prc.keysight.com/Content/PDF_Files/5989-7894EN.pdf), [Fluke diode testing](https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-test-diodes).
