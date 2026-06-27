# Expanded component failure modes

> tags: component, failure-mode, capacitor, resistor, inductor, relay, optocoupler, tvs, mosfet, crystal, connector

Component-level diagnosis works best when each part is treated as a failure mode plus a circuit role, not as an isolated object.

## Capacitors
- **Electrolytic:** high ESR, low capacitance, leakage, venting, dried electrolyte, ripple heat. Symptoms: reset loops, SMPS ticking, ripple, startup failure.
- **MLCC:** short from cracking, capacitance loss under DC bias, intermittent under flex. Symptoms: rail short, noise, intermittent sensor faults.
- **Film/safety caps:** open or reduced capacitance, cracking; replace X/Y capacitors only with same safety class.

## Resistors and shunts
- Thick-film resistors can drift high after overload.
- Fusible resistors may open intentionally.
- Shunts crack or desolder, causing wrong current sense or no output.
- High-value bias resistors in SMPS startup or feedback can drift/open and cause no-start.

## Inductors and transformers
- Open winding, shorted turns, cracked solder, saturation from wrong replacement, audible noise under overload.
- In buck converters, a cracked inductor joint can cause intermittent rail drop.
- In flybacks, primary/secondary shorts are serious isolation failures.

## Diodes, TVS, Zeners
- Shorted TVS clamps a rail after surge.
- Open diode removes flyback/catch path and destroys switches.
- Leaky Zener/reference shifts regulation or sensor protection threshold.
- Bridge rectifier shorts blow fuses or current-limit supplies.

## MOSFETs and drivers
- EOS commonly leaves low-ohmic shorts between terminals.
- Gate oxide damage causes leakage, false turn-on, or dead gate.
- Avalanche/inductive stress damages output stages.
- Check driver IC and gate resistors after MOSFET failure.

## Relays
- Coil open, coil short, contact pitting, contact welding, high contact resistance, cracked solder joints.
- A relay can click and still have bad contacts.
- Test under load, not just coil continuity.

## Optocouplers
- LED open or weak CTR, output transistor leakage, slow switching with age/heat.
- In SMPS feedback, a weak optocoupler can cause unstable or high output.

## Crystals/resonators
- Cracked package, broken solder, contamination, bad load capacitors.
- Failure mimics dead MCU with good rails.

## Connectors
- Fretting, corrosion, loose pins, cracked solder anchors, melted housings, poor contact normal force.
- Always voltage-drop test high-current pins under load.

Sources: [Nexperia MOSFET EOS signatures](https://assets.nexperia.com/documents/application-note/AN11243.pdf), [Vishay automotive MOSFET failures](https://www.vishay.com/docs/69294/an910.pdf), [Fluke diode testing](https://www.fluke.com/en-us/learn/blog/digital-multimeters/how-to-test-diodes), [IPC-A-610 training description](https://stiusa.com/product/ipc-a-610-certified-ipc-trainer-cit-certification-program-lecture-based/), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf).
