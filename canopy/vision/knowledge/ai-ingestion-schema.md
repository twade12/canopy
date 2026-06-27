# AI ingestion schema for PCB triage cases

> tags: ai, schema, ingestion, retrieval, case-history, structured-data, triage

Use a consistent schema so an AI system can retrieve practical troubleshooting steps, compare similar failures, and recommend next tests without inventing measurements.

## Recommended markdown front matter
```yaml
title: "Short descriptive case or knowledge card title"
tags: [automotive, ecu, no-comms, can, power]
module_family: "PCM | TCM | BCM | FICM | appliance | industrial | unknown"
board_id: "optional"
symptom: "observable symptom"
fault_block: "power | comms | input | output | mcu | solder | corrosion | unknown"
confidence: "confirmed | probable | hypothesis"
safety_level: "low-voltage | automotive-12v | mains | hv | srs/safety-critical"
requires_authorization: true
```

## Case record template
```markdown
# Case: <module> — <symptom>

> tags: case, <module-family>, <symptom>, <fault-block>

## Symptom
- Observable fact only.

## Board / module
- Part number, revision, date code, connector count, photos.

## Setup
- Supply voltage/current limit, grounds, wake lines, loads, comms termination, tools.

## Measurements
| Point | Expected | Measured | Tool | Interpretation |
|---|---:|---:|---|---|

## Fault isolation
- Step-by-step evidence.

## Root cause
- Confirmed cause and independent confirmation.

## Repair
- Part removed/replaced/reworked, replacement details, rework method.

## Verification
- Original symptom retest, stress test, pass/fail values.

## Lessons / retrieval notes
- What future cases should search for.
```

## Retrieval design
- Use tags for symptoms and board blocks: `no-power`, `no-comms`, `short`, `sensor-ref-low`, `output-dead`, `intermittent`, `water-damage`, `reset-loop`, `programming`.
- Store exact values. “5 V good” is less useful than “U3 pin 5 = 5.03 V, ripple 18 mVpp.”
- Store negative tests. They prevent repeated work.
- Store confidence and safety level so the AI does not recommend unsafe procedures casually.

## Recommendation rule for the AI
- A recommendation must include: precondition, measurement, expected result, interpretation, and next branch.
- Do not recommend replacement unless the fault is confirmed or the replacement is explicitly framed as a test with risk.
- For safety/security/emissions systems, recommend authorized procedures and verification, not bypasses.

Sources: [IPC Standards](https://www.electronics.org/ipc-standards), [Vector CAN physical layer problems](https://cdn.vector.com/cms/content/know-how/_application-notes/AN-ANI-1-115_HS_Physical_Layer_Problems.pdf), [NASA-STD-8739.3](https://nepp.nasa.gov/docuploads/06AA01BA-FC7E-4094-AE829CE371A7B05D/NASA-STD-8739.3.pdf).
