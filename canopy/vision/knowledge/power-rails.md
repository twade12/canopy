# Tracing power lines and rails

> tags: power, rails, voltage, regulator, LDO, ground, no-power, fuse, KL30, KL15, inrush

Power faults masquerade as everything else, so prove the supply chain before chasing logic.

## Map the supply chain from the connector inward
1. **Permanent power (KL30 / B+):** at the battery via a fuse — live with ignition off.
2. **Switched power (KL15 / ignition):** via the ignition switch or a relay.
3. **Grounds:** power ground(s) and, sometimes, a separate signal/analog ground.
4. On-board the raw 12 V feeds reverse-polarity protection (series diode/FET) and a fuse, then
   one or more regulators: a linear LDO or a switching (buck) converter producing the logic
   rails — typically 5.0 V and/or 3.3 V — plus possibly a protected sensor 5 V reference.

## The no-power / no-comms flow
- Set DMM to DC, black probe on a known-good chassis/board ground.
- Confirm **ground** continuity first: <0.1 V drop from the connector ground pin to board ground
  under load. A bad ground imitates a dead module.
- Confirm raw **12 V** reaches the board past the fuse and reverse-protection device. No 12 V on
  one side of a series diode/FET but present on the other → that protection device or fuse is
  open (often from a prior reverse-hookup or downstream short).
- Confirm each **logic rail** at the regulator output: 5.0 V should read ~4.9–5.1 V; 3.3 V ~3.2–3.4 V.
  - **Rail low or zero:** is the regulator getting its input? If yes and output is dead/low →
    the regulator is bad OR something downstream is pulling it down. Lift the regulator's load
    or sectionalize to tell which.
  - **Rail present but MCU dead:** check the reset line and clock before condemning the MCU.

## Current signature tells you a lot
- Set the bench PSU current limit to just above expected quiescent BEFORE energizing.
- **Inrush** spikes then settles — large/sustained draw = short (suspect a shorted decoupling or
  bulk cap, a shorted transceiver/driver, or reverse-protection FET).
- **Quiescent far above spec** = partial short; sweep the board with a thermal camera or finger —
  the faulting part heats first. **Near-zero draw** = open supply path upstream of the load.

## Common power-path faults on automotive modules
- Open reverse-polarity diode/FET or input fuse after a jump/reverse event.
- Failed/bulged electrolytic on the raw or regulated rail (ripple, sag, reset loops).
- Cold/cracked solder on the connector power/ground pins or a heatsinked regulator.
- Switching regulator with a dry inductor joint or shorted catch diode.

Sources: [Bettlink – Test an ECU with a multimeter](https://www.bettlink.com/blog/how-to-test-an-ecu-with-a-multimeter-complete-guide),
[Aivon – PCB power issues](https://www.aivon.com/blog/pcb-knowledge/troubleshooting-pcb-power-issues-a-systematic-approach-to-diagnosis-and-repair/).
