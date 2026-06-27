# Automotive front-end protection and input power path

> tags: automotive, load-dump, reverse-polarity, tvs, fuse, input-protection, battery, kl30, kl15, transient

Automotive modules live on a hostile supply. Do not judge the board by “12 V” alone. The front end must survive reverse battery, load dump, cranking dips, jump starts, inductive switching, ESD, moisture, and harness faults.

## Typical front-end chain
- Connector B+ / KL30 / KL15.
- Input fuse, fusible resistor, PTC, or PCB trace fuse.
- Reverse-polarity protection: series diode, P-channel MOSFET, N-channel ideal-diode controller, or protected high-side stage.
- Transient suppression: TVS diode, MOV, RC snubber, common-mode choke, EMI filter, bulk capacitor.
- Pre-regulator or buck converter for 5 V/3.3 V logic.
- Protected sensor reference and protected output supplies.

## Common front-end faults
- Shorted TVS after load dump or jump-start event.
- Open reverse-protection diode/FET after reverse polarity or downstream short.
- Open trace fuse or current-sense element after overload.
- Cracked input MLCC or electrolytic causing direct short or high ripple.
- Corroded connector pin causing voltage drop only under load.
- Failed buck controller after overvoltage transient.

## Load-dump and transient reasoning
- Load dump can occur when a battery disconnects while the alternator is generating current and other loads remain connected.
- If several modules from the same vehicle arrive with front-end damage, suspect vehicle-level transient or battery/charging/wiring event.
- A shorted TVS may be the sacrificial evidence of a larger event; replace it only after checking downstream regulators and caps.

## Reverse-polarity protection checks
- For a series diode: measure forward drop in diode mode and voltage drop under load.
- For MOSFET reverse protection: identify source/drain/body diode orientation and gate drive. Check D-S short, gate leakage, and controller supply.
- If 12 V exists at connector but not after protection, determine whether the protection device is open or intentionally off due to controller/enable fault.

## Input ripple and bulk capacitance
- Scope raw input under load. Excessive ripple or dips can reset regulators and MCU even when a DMM reads “12 V.”
- Replace bulk electrolytics with automotive-temperature, low-ESR parts when ripple current and environment demand it.
- Verify polarity and voltage rating; automotive 12 V boards often need much more than 16 V margin at the input.

## Replacement rules
- Use AEC-qualified parts when replacing semiconductors or passives in vehicle modules when possible.
- Match TVS working voltage, standoff voltage, clamping behavior, power rating, unidirectional/bidirectional type, and package.
- Match reverse FET voltage, current, RDS(on), gate threshold class, SOA, avalanche capability, package thermal resistance, and pinout.

Sources: [TI automotive reverse polarity reference design](https://www.ti.com/lit/ug/tiduc42/tiduc42.pdf), [TI load dump over-voltage protection](https://www.ti.com/lit/pdf/snva190), [TI reverse battery protection note](https://www.ti.com/lit/SNOAA94), [ISO 16750 overview](https://www.iso.org/standard/69568.html), [AEC Documents](https://www.aecouncil.com/AECDocuments.html).
