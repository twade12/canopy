# Glossary for PCB triage and automotive electronics

> tags: glossary, terminology, automotive, electronics, pcb, repair

## Power and vehicle terms
- **B+ / KL30:** permanent battery positive supply.
- **KL15:** ignition-switched supply.
- **Wake line:** signal that tells a module to leave sleep/standby.
- **Load dump:** automotive overvoltage transient caused by battery disconnection while alternator current is present.
- **Reverse polarity:** accidental reversed battery/supply connection.
- **Quiescent current:** steady current draw in sleep/idle state.
- **Inrush current:** initial current surge when capacitors and converters start.

## Board diagnosis terms
- **Rail:** named supply voltage net such as 5 V, 3.3 V, Vref, VBAT.
- **Sectionalize:** isolate a fault by dividing the board into smaller powered or connected regions.
- **Current injection:** applying controlled low-voltage current to a shorted rail to find heat/voltage-drop evidence.
- **Voltage drop test:** measuring voltage across a connection under load to find resistance.
- **Diode mode:** DMM mode that measures semiconductor junction forward voltage.
- **ESR:** equivalent series resistance, important for electrolytic and regulator stability.

## Communication terms
- **CAN:** differential automotive/industrial network.
- **CAN FD:** CAN with flexible data rate and larger payload.
- **LIN:** low-cost single-wire automotive sub-bus.
- **K-line:** older single-wire diagnostic communication line.
- **SENT:** Single Edge Nibble Transmission, unidirectional sensor-to-ECU interface.
- **PSI5:** Peripheral Sensor Interface 5, two-wire automotive sensor interface.
- **Transceiver:** physical-layer IC between logic controller and bus wiring.
- **Termination:** resistor network controlling transmission-line reflections.

## Component terms
- **TVS:** transient voltage suppressor, usually sacrificial surge clamp.
- **LDO:** low-dropout linear regulator.
- **Buck converter:** switching converter that steps voltage down.
- **Flyback diode:** diode that clamps inductive kick when a coil is switched off.
- **High-side switch:** switch between supply and load.
- **Low-side switch:** switch between load and ground.
- **H-bridge:** four-switch circuit for bidirectional motor control.
- **Shunt:** low-value resistor used to measure current.
- **MOV:** metal-oxide varistor, common mains surge protector.

## Rework terms
- **Reflow:** heating solder joints until solder melts and reforms.
- **Rework:** correcting or replacing components to meet original requirements.
- **Repair:** restoring function when original materials/features are damaged.
- **MSL:** moisture sensitivity level for reflow-sensitive packages.
- **No-clean flux:** flux designed to leave benign residues under qualified process conditions; heavy hand residues may still need cleaning.
- **Conformal coating:** protective polymer coating over PCB assemblies.
- **Potting:** encapsulating electronics in resin or compound.

Sources: [IPC Standards](https://www.electronics.org/ipc-standards), [TI CAN physical layer requirements](https://www.ti.com/lit/pdf/slla270), [NXP LIN transceiver](https://www.nxp.com/products/interfaces/automotive-lin-solutions/lin-transceiver%3ATJA1020), [SAE J2716 SENT](https://www.sae.org/standards/j2716-sent-single-edge-nibble-transmission-automotive-applications), [ISO 16750 overview](https://www.iso.org/standard/69568.html).
