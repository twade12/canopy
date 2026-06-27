# Automotive communications beyond basic CAN/LIN/K-line

> tags: automotive, communication, can-fd, flexray, sent, psi5, ethernet, transceiver, physical-layer

Modern modules may use CAN, CAN FD, LIN, K-line, SENT, PSI5, FlexRay, Ethernet, or proprietary sensor/actuator links. Physical-layer checks still come first: power, ground, termination/bias, waveform, and transceiver behavior.

## CAN FD
- CAN FD uses the same basic differential bus idea as CAN, but can switch to a faster data phase.
- Physical-layer troubleshooting still starts with termination, common-mode voltage, clean differential waveform, correct transceiver supply, and correct bus topology.
- Mixed CAN/CAN FD networks can create confusing errors if non-FD nodes see FD traffic without proper handling.

## FlexRay
- FlexRay is a high-speed deterministic automotive bus using differential signaling.
- Scope both lines and look for mirror-image behavior, coincident edges, and correct amplitude.
- Because FlexRay is time-triggered, a node may appear silent if startup/synchronization conditions are not met.

## SENT / SAE J2716
- SENT is a unidirectional single-wire sensor-to-ECU interface using pulse timing rather than analog voltage level.
- Do not diagnose SENT like a variable analog sensor. Scope pulse timing and decode nibbles if possible.
- Check sensor supply, ground, pull-up/bias, signal idle level, and edge quality.

## PSI5
- PSI5 is a two-wire automotive sensor interface often used in airbag/safety sensor contexts.
- It commonly combines power and data behavior, so missing current modulation may be supply, sensor, harness, or receiver fault.
- Use extreme caution with SRS systems; use approved simulators and procedures only.

## Automotive Ethernet
- Check connector, magnetics/common-mode chokes, PHY supplies, reference clock, link status, and cable pair integrity.
- Do not assume no IP traffic means physical failure; first check link negotiation and PHY activity LEDs/registers where accessible.

## General transceiver checks
- Verify transceiver supply and ground directly at the IC.
- Check bus pins for shorts to ground, battery, 5 V, each other, or shield.
- Check logic-side TX/RX pins for stuck states.
- Compare suspect transceiver diode-mode readings against a known-good channel or board.
- A hot transceiver, wrong bus bias, or dominant-stuck line is a prime physical-layer suspect.

Sources: [TI CAN physical layer requirements](https://www.ti.com/lit/pdf/slla270), [TI CAN debugging](https://www.ti.com/lit/pdf/slyt529), [TI CAN FD MCAN app note](https://www.ti.com/lit/pdf/slaaet4), [Vector CAN physical layer problems](https://cdn.vector.com/cms/content/know-how/_application-notes/AN-ANI-1-115_HS_Physical_Layer_Problems.pdf), [Pico FlexRay physical layer test](https://www.picoauto.com/library/automotive-guided-tests/communication/flexray-bus/AGT-125-flexray-bus-physical-layer/), [SAE J2716 SENT](https://www.sae.org/standards/j2716-sent-single-edge-nibble-transmission-automotive-applications), [Pico PSI5 decoding](https://www.picotech.com/library/knowledge-bases/oscilloscopes/psi5-serial-protocol-decoding).
