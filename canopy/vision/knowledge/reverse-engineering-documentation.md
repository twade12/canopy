# Reverse-engineering documentation workflow

> tags: reverse-engineering, documentation, schematic, netlist, photos, pinout, case-history, ai-ingestion

The goal of reverse engineering for repair is not a beautiful complete schematic. The goal is a reliable enough model of the suspect block to isolate the fault and make future identical boards faster.

## Case folder structure
- `photos/raw/` — untouched intake photos.
- `photos/annotated/` — connector pins, rails, blocks, suspect parts, measurements.
- `pinout.md` — connector pin table with confidence level and source.
- `block-map.md` — board-level functional blocks.
- `measurements.md` — all measurements with date, instrument, setup, and result.
- `partial-schematics/` — focused drawings for power, comms, input, or output blocks.
- `repair-log.md` — symptom, hypothesis, evidence, repair, and verification.

## Pinout confidence levels
- **A — verified from OEM/service data:** reliable unless variant mismatch exists.
- **B — verified by board tracing:** connected to obvious block and measured safely.
- **C — inferred by topology:** probable but not safe for power-up without confirmation.
- **D — unknown:** do not energize.

## Measurement note format
- `Board:` part number, revision, date code, module family.
- `Symptom:` observable fact.
- `Setup:` supply voltage/current limit, grounds used, loads connected, wake lines, CAN/LIN termination.
- `Point:` connector pin/component pin/net name.
- `Expected:` value or behavior.
- `Measured:` value and instrument.
- `Interpretation:` what the measurement proves and what it does not prove.
- `Next action:` smallest next test.

## Partial schematic rules
- Draw only the suspect block and its dependencies.
- Label every component with board designator if visible; otherwise assign temporary labels such as `U? CAN transceiver`, `R? CANH series`, `D? TVS`.
- Mark unknown values as unknown. Do not invent resistor values or rail voltages.
- Show connector pins, protection parts, active devices, pull-ups/pull-downs, feedback dividers, loads, and test pads.

## AI-ready repair case record
- Use consistent headings: `Symptom`, `Board family`, `Pinout`, `Power state`, `Measurements`, `Fault isolation`, `Root cause`, `Repair`, `Verification`, `Lessons`.
- Include negative evidence: “5 V rail present, reset high, no clock” is more useful than “MCU dead.”
- Include substitute part data: original marking, package, pinout, replacement, reason accepted, and any changes.
- Include final pass/fail criteria so the AI can recommend a complete lifecycle, not just a component swap.

## Common documentation mistakes
- Recording only the replaced part, not the measurement that proved it bad.
- Forgetting the current limit, wake state, load, or CAN termination used during test.
- Mixing harness-side and board-side connector pin numbering.
- Reworking multiple parts before re-measuring.
- Saving only cropped photos that remove context.

Sources: [IPC 7711/7721 Revision D](https://shop.electronics.org/ipc-771121/ipc-771121-standard-only/Revision-d/english), [Vector CAN physical layer problems](https://cdn.vector.com/cms/content/know-how/_application-notes/AN-ANI-1-115_HS_Physical_Layer_Problems.pdf), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf).
