# Automotive module family patterns

> tags: automotive, ecu, pcm, tcm, ficm, bcm, abs, hvac, cluster, headlight, module-family

Module family tells you which blocks deserve early attention. Do not use this to skip measurement; use it to rank hypotheses.

## ECU / PCM
- Common blocks: battery/ignition input, multiple 5 V sensor references, crank/cam inputs, injector/coil drivers, H-bridge or low-side outputs, CAN/LIN/K-line, EEPROM/Flash.
- Common failures: input protection, sensor reference short, driver blown by shorted actuator, electrolytic/ripple reset, CAN transceiver damage, clock/reset issue, water intrusion.
- First checks: power/ground voltage drop, 5 V refs, current signature, reset/clock, CAN physical layer, suspect output driver.

## TCM
- Common blocks: solenoid drivers, pressure sensor inputs, speed sensor inputs, CAN, EEPROM/adaptation data, high-current drivers.
- Common failures: solenoid driver damage, cracked solder from heat/vibration, fluid intrusion, sensor supply faults, corrupted adaptation/data, overheated power stages.
- First checks: transmission connector pins, solenoid output resistance, dummy loads, driver stage, power rails, CAN.

## FICM / injector modules
- Common blocks: high-current injector drivers, boost/high-voltage generation, current sensing, gate drivers, logic control.
- Common failures: power stage MOSFETs, driver ICs, high-voltage caps, cracked solder, poor supply/ground, thermal damage.
- First checks: input current, high-voltage generation only under safe controlled conditions, driver shorts, gate drive, load simulator.

## BCM / body control
- Common blocks: many high-side/low-side smart outputs, relay drivers, LIN, CAN, wake/sleep current management.
- Common failures: water intrusion, shorted outputs from lamps/locks/windows, connector corrosion, parasitic draw, LIN transceiver failures.
- First checks: quiescent current, wake lines, outputs with dummy loads, LIN/CAN physical layer, connector corrosion.

## ABS / brake / steering modules
- Common blocks: motor/pump drivers, solenoid drivers, wheel-speed inputs, CAN, safety monitoring.
- Common failures: high-current motor driver/relay, solder cracks, pump motor load issues, sensor input faults.
- Safety note: brake/steering modules require strict authorization and full functional validation; do not bypass safety functions.

## HVAC / climate modules
- Common blocks: blower motor control, blend-door motor drivers, temperature sensors, pressure sensor inputs, AC clutch/relay command, LIN/CAN.
- Common failures: MOSFET/driver overheating, relay/connector damage, motor stalls, sensor ref faults, solder cracks.
- First checks: outputs into dummy loads, motor current, sensor refs, wake/comms.

## Headlight / lighting modules
- Common blocks: LED drivers, step-up/step-down converters, LIN/CAN, thermal sensing, motor/leveling outputs.
- Common failures: water intrusion, LED driver faults, corroded connectors, failed current sense, thermal damage, cracked solder.
- First checks: input protection, LED driver rails, current sense, output current limits, communication wake.

Sources: [AllPCB common ECU faults](https://www.allpcb.com/allelectrohub/common-ecu-faults-and-diagnostic-procedures), [Infineon automotive application guide](https://community.infineon.com/gfawx74859/attachments/gfawx74859/cnblogs/14418/4/Infineon-Automotive-Application-Guide-2016-ABR-v02_00-EN.pdf), [Nexperia driving automotive solenoids](https://www.nexperia.com/applications/interactive-app-notes/IAN50003_driving-automotive-solenoids), [ISO 16750 overview](https://www.iso.org/standard/69568.html), [AEC Documents](https://www.aecouncil.com/AECDocuments.html).
