# Parts replacement and substitution rules

> tags: replacement, sourcing, substitution, datasheet, aec, capacitor, mosfet, diode, regulator, relay

A replacement part must match the circuit role and stress environment, not just the printed number. Wrong substitutions can pass a bench test and fail in the vehicle, appliance, or industrial environment.

## Universal substitution checklist
- Package, footprint, pinout, orientation, thermal pad, and height.
- Absolute maximum ratings and normal operating range.
- Temperature grade and automotive/industrial qualification when needed.
- Electrical parameters that matter in the circuit role.
- Failure behavior and protection features.
- Soldering/reflow limits and moisture sensitivity.
- Availability from traceable suppliers.

## Capacitors
- Match capacitance, voltage, polarity, ESR class, ripple current, temperature rating, lifetime, package, and dielectric.
- Electrolytic replacement: same capacitance, equal/higher voltage, equal/higher temperature and ripple rating, appropriate ESR.
- MLCC replacement: consider DC bias, voltage rating, dielectric class, and mechanical cracking risk.
- Do not replace output caps in switching regulators with arbitrary ESR changes; loop stability can change.

## MOSFETs
- Match N/P channel, voltage, current, RDS(on), VGS rating, gate threshold class, gate charge, SOA, avalanche rating, package thermal resistance, and pinout.
- Logic-level gate threshold is not enough; check RDS(on) at actual gate voltage.
- For automotive inductive loads, avalanche/SOA and thermal behavior matter as much as current rating.

## Diodes and TVS parts
- Rectifier/catch diode: match voltage, current, speed/recovery, package, thermal, and surge.
- Schottky: check reverse leakage at temperature.
- TVS: match standoff voltage, breakdown, clamp voltage, pulse power, uni/bidirectional type, capacitance if on communication lines.

## Regulators and drivers
- Match output voltage, dropout/switching frequency/current limit, enable polarity, power-good behavior, pinout, package thermal pad, and stability capacitor requirements.
- Smart switches must match diagnostics and protection behavior, not just current rating.

## Relays and electromechanical parts
- Match coil voltage/current, contact rating, contact material, footprint, pinout, sealed/unsealed type, temperature, and load type.
- Contact rating for resistive loads does not automatically apply to inductive or motor loads.

## AEC and environmental requirements
- Prefer AEC-Q100 ICs, AEC-Q101 discretes, and AEC-Q200 passives for automotive module repair when the original was automotive-grade.
- Match temperature range: underhood and transmission modules need far more margin than cabin electronics.
- Use conformal coating compatibility and vibration resistance as replacement criteria.

Sources: [AEC Documents](https://www.aecouncil.com/AECDocuments.html), [AEC-Q100 base document](https://www.aecouncil.com/Documents/AEC_Q100_Rev_J_Base_Document.pdf), [IPC/JEDEC J-STD-020](https://shop.electronics.org/ipcjedec-j-std-020/ipcjedec-j-std-020-standard-only?f%5B0%5D=language%3A37), [Nexperia MOSFET EOS signatures](https://assets.nexperia.com/documents/application-note/AN11243.pdf), [TI reverse battery protection note](https://www.ti.com/lit/SNOAA94).
