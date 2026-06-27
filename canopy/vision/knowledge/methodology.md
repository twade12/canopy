# Root-cause methodology for an unknown module

> tags: methodology, diagnosis, root-cause, strategy, bring-up, divide-and-conquer

This is the master playbook for triaging a circuit board you have never seen before, given
only a stated symptom. Work it top to bottom. Never skip the power-up order. Never energize an
unverified power/ground assignment.

## 1. Frame the problem before touching it
- Write the symptom as an observable fact ("no comms on the bench", "B+ fuse pops on power-up",
  "wakes but one output dead"), not a guess.
- Pull the module's pinout (from the wiring diagram) and identify, on the connector: permanent
  power (KL30/B+), switched power (KL15/ignition), grounds, comms (CAN-H/L, LIN, K-line), wake/
  enable lines, and the suspect output(s). Everything downstream is reasoned from these pins.
- Form 2–3 candidate hypotheses ranked by prior probability for this class of module
  (e.g. electrolytic caps on a 1990s–2010s board, cold joints on connector/heatsink pins,
  a blown output driver on a shorted-actuator complaint).

## 2. Inspect, then bring power up in order
- **Visual first** (loupe / microscope): corrosion, burnt/discolored parts, bulged or vented
  electrolytics, cracked or cold solder joints (especially connector pins, heatsink-mounted
  power devices, and large connectors), lifted pads, water marks, prior rework.
- **Power-up order is non-negotiable:** GROUND first → permanent 12 V (current-limited) →
  switched/ignition → any separate reference rails. Set the PSU current limit per expectation
  BEFORE energizing. Watch inrush and quiescent current — a quiescent draw far above spec means
  a short (suspect a shorted cap, transceiver, or driver); near-zero means an open supply path.

## 3. Divide and conquer (sectionalize)
The fastest path to root cause is halving the suspect area, not testing parts at random.
- Split the board into functional blocks: power supply, MCU + its support (clock, reset, EEPROM),
  communications, input conditioning (sensors), output drivers. Confirm each block's
  precondition before blaming the next: no clean 5 V rail → do not chase a "dead MCU".
- Trace from a known-good reference toward the fault. Follow the actual net from the connector
  pin to the first active device on it.
- When a rail is wrong, sectionalize it: lift a suspect component or (last resort) cut a trace to
  see which side holds the fault. Localize a short with the low-voltage "voltage-drop / µV
  injection" method or a thermal camera (the shorted part gets warm first).

## 4. Verify the fault, then repair, then re-verify
- **Confirm** the root cause with a second, independent measurement before replacing anything
  (e.g. cap measured open AND the rail it feeds shows ripple/sag). Replacing on suspicion alone
  is how you create intermittent comebacks.
- Repair, then **re-verify against the original symptom** under the same conditions that showed
  it. A fix that isn't re-tested isn't a fix.
- Record: symptom → measurements (with the pin/component and value) → root cause → repair action.
  These become the team's case history and make the next identical board a 5-minute job.

## Golden rules
- Reason from the real pinout and what you can measure — never from invented voltages or
  assumed physics.
- One change at a time; re-measure after each.
- A ground problem mimics almost any fault. Verify grounds early (<0.1 V drop under load).
- "It's probably the caps" is a hypothesis, not a diagnosis. Prove it.

Sources: [AllPCB – Common ECU faults](https://www.allpcb.com/allelectrohub/common-ecu-faults-and-diagnostic-procedures),
[Accelerated Assemblies – PCB troubleshooting, fault to fix](https://www.acceleratedassemblies.com/blog/pcb-troubleshooting-guide-for-engineers--from-fault-to-fix),
[Aivon – Systematic PCB power diagnosis](https://www.aivon.com/blog/pcb-knowledge/troubleshooting-pcb-power-issues-a-systematic-approach-to-diagnosis-and-repair/).
