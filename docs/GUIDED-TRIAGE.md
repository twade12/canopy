# Guided Triage — physics-first repair walkthrough

> Goal: let *anyone* (not just an EE) take a sealed, unknown module + a customer symptom and be
> walked, one simple step at a time, from the cheapest non-invasive checks to board-level
> diagnosis — producing a complete, documented repair (wiki page) per unit. Target throughput:
> many quotes/day, each fully documented, with knowledge compounding across jobs.

## Principle
Always recommend the **single simplest, safest, most-informative next action**, grounded in the
real pinout + the CANOPY knowledge base, and adapt to the recorded result. Never invent values.
Cheap/non-invasive before expensive/invasive. Confirm before replacing; re-verify after repair.

## Phases (simple → complex)
1. **Intake** — identity (photos of label/connector, part number) + the customer's symptom(s).
   Creates/updates the project record + tags.
2. **Sealed checks (non-invasive)** — visual of case/connector/pins; identify power/ground/CAN
   pins from the diagram; resistance across power↔ground and CAN-H↔CAN-L (≈60 Ω), continuity.
3. **Bench power-up** — current-limited PSU on KL30/KL15/GND; inrush + quiescent current; wake;
   is there any comms? (catches shorts and dead modules before opening).
4. **Open & inspect** — open the case, photograph the board (→ PCB tab auto-analyzes), visual for
   burnt/corroded parts, bulged caps, cracked/cold solder.
5. **Board-level checks** — rails (5 V/3.3 V), MCU clock/reset, comms transceiver bias, then the
   components most implicated by the symptom — progressively.
6. **Root cause & repair** — confirm the fault with a second independent measurement; repair;
   re-verify against the original symptom.
7. **Document** — compile the wiki page (pinout + board components + annotated photos + the step
   log + root cause + repair + verification).

## How it compiles the existing tabs (no parallel data)
The guided flow is an orchestrator over what CANOPY already stores — it *drives* the other tabs
rather than duplicating them:
- Intake identity/tags → the **Record**.
- Diagram upload + pin extraction → **Diagram/Pinout**.
- Board photos → **PCB** (boxed components, corrections).
- Each recorded step (measurement + result) → the **guided log** (a `guided` message channel) and
  salient findings → **Memories** (the compounding case history).
- Phase 7 → the **Wiki** (already compiles all of the above).

## Engine
- `extract.guided_next(...)` asks the model for the next step as JSON
  `{phase, title, why, how, tool, expected, record, safety, done, root_cause, repair}`, given the
  module identity + pinout, the relevant KB articles (`kb.context_block`), the current phase, the
  symptom, and the log of completed steps + results.
- `POST /api/vehicles/{id}/guided/next` → next step. `POST .../guided/step` records a completed
  step (status pass/fail/note + value) into the `guided` channel. `GET .../guided/log` returns it.
- The front-end **Guided** tab shows the phase ladder, the current recommended step
  (why/how/tool/expected/what-to-record/safety), result inputs, and the running log, then a
  "Compile wiki" hand-off.

## Staging
- **v1 (this iteration):** the engine + Guided tab loop (suggest → record → adapt) over the
  existing triage/KB/pinout; log persists; wiki hand-off.
- **v2:** tighter tab orchestration (auto-open PCB on the "photograph board" step, pull pin IDs
  into sealed-check steps), per-step photo capture inline, quote/cost fields.
- **v3:** templated phase plans per module family; pass/fail gating; multi-tech queue dashboard.
