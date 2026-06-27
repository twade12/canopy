# CANOPY — Long-Term Gameplan

> **Vision.** A *context driver* for repair and remanufacturing of automotive and industrial
> electronic modules: an ever-learning digital assistant and note-taker that aggregates every
> diagram, board photo, bench test, and repair a team has ever done, and uses that collective
> memory to guide a technician — step by step — from symptom to root cause to verified fix,
> and then writes the report and the wiki entry automatically. The human still does the
> physical work; the AI is the guide that never forgets a previous case.

This document is the roadmap from today's single-box app to a multi-technician team service.
For the bench station hardware track see [HARDWARE.md](HARDWARE.md) and
[BATTLE-PLAN.md](BATTLE-PLAN.md); for deploying the current app see [DEPLOY.md](DEPLOY.md).

---

## Where we are today (foundation in place)

- **Vision app** ([canopy/vision/](../canopy/vision/)): upload a wiring diagram (image/PDF) →
  AI identifies the project, extracts the pinout (now schematic-aware, with layout-reconstructed
  text), drafts a CAN bench plan, chats per-project, and accumulates **embedding-deduplicated
  memories**. A **global Assistant** answers across all projects. A **dockable VS Code-style UI**
  with streaming, a live AI-activity toast, and a cancel control.
- **CAN bench** ([bench.py](../canopy/vision/bench.py)): connect to a USB-to-CAN/SocketCAN/virtual
  bus, confirm ECU connectivity (tester-present + VIN + DTCs), send frames, run UDS, watch traffic.
- **Deep research** ([research.py](../canopy/vision/research.py)): pluggable web search →
  sourced links + images to fill knowledge gaps.
- **Hosting**: cookie auth + login, `systemd` + nginx deploy.
- **CAN/sim stack** ([canopy/sim/](../canopy/sim/), [canopy/hal/](../canopy/hal/)): restbus with
  E2E, UDS client/server — the "car in a box".

The gaps to "usable by a whole team" are: a real multi-user data model, the guided
repair-session workflow, PCB-photo triage, phone capture, report/wiki generation, and the
infra to run it reliably for many people at once.

---

## Target workflow — the guided repair session

The core loop we are building toward, as a first-class object (`RepairSession`):

1. **Intake.** Tech creates/loads a *module* (e.g. "2016 F-250 6.7L PCM, no-start"), or scans a
   part/board. Symptom captured.
2. **Guide.** The assistant, drawing on all prior cases for similar modules, proposes the **next
   thing to check** — a pin to back-probe, a rail to measure, a component to inspect — and **which
   tool** to use (multimeter, oscilloscope, bench PSU, function generator, thermal camera).
3. **Observe.** Tech performs the physical check and **records the result** (a value, a pass/fail,
   a photo of the board/scope screen). Phone capture (below) makes this frictionless.
4. **Iterate.** The new evidence updates the assistant's hypothesis; it asks the next question.
   Back-and-forth until a **root cause** is identified (e.g. "U3 5V LDO open", "cracked solder at
   CAN transceiver", "corroded pin 12").
5. **Fix & verify.** Repair action recorded; verified on the CAN bench (connectivity + function,
   e.g. command the A/C clutch relay and confirm output).
6. **Publish.** The session auto-renders a **detailed repair report** (PDF/Markdown) and a
   **wiki entry** (symptom → checks → root cause → fix → verification), which becomes training
   data and memory for the next tech who sees the same module.

This is the `Case`/wiki loop from [CLAUDE.md](../CLAUDE.md) §6/§7.5, realized as an interactive,
multimodal, AI-guided session.

---

## Workstreams & phases

### Phase 1 — Multi-user & data model (unlocks "a team")
- **Accounts & roles.** Replace the single shared password with real users (tech/engineer/admin),
  org/workspace scoping, per-action attribution. Keep it simple: email+password or SSO (Authentik/
  Google) behind the existing middleware; sessions already cookie-based.
- **Postgres + pgvector.** Migrate the vision store from SQLite to the Postgres/Timescale/pgvector
  already in [docker-compose.yml](../docker-compose.yml). Embeddings become first-class vector
  columns (semantic search across the whole org's knowledge, not per-process). Object storage
  (S3/MinIO) for diagrams/photos instead of local disk.
- **Domain objects.** `Workspace → Module → RepairSession → Observation/Photo → Case`, plus
  `Project` for triage. Provenance on every memory (who/when/which session).

### Phase 2 — Guided repair sessions + PCB triage
- **Session engine.** A stateful, multimodal chat tied to a module: the model is given the
  module's pinout, prior cases (RAG), and the running observation log; it returns a *next-step*
  recommendation + the tool to use, and a structured slot to record the result.
- **PCB component identification.** Upload a board photo (whole ECU or a region) → the multimodal
  model identifies components (ICs, regulators, transceivers, FETs, connectors), states likely
  **function**, **what to check** on each (continuity, rail voltage, waveform, temperature), and
  **which instrument** to use. Pair with reference search (Phase research) for datasheets.
- **Protocol awareness.** Identify the serial/diagnostic protocols a module uses (CAN, CAN-FD,
  **J1939**, **J1850/SAE**, K-line, LIN, GMLAN) and the **OBD-II connector pinout** so a tech can
  wire to the right pins. (Seed this as built-in reference knowledge + research.)

### Phase 3 — Phone capture & real-time field input
- **Pair a phone to a session.** From the desktop session, show a QR code → opens a minimal
  mobile capture page bound to that session via a short-lived signed token (same HMAC scheme as
  [auth.py](../canopy/vision/auth.py)). The tech photographs the board/scope as they work and
  images stream into the session in real time, immediately available to the AI.
- **Offline-tolerant uploads** (retry/queue) for shop-floor Wi-Fi.

### Phase 4 — Reports & wiki generation
- **Report builder.** Render a `RepairSession` to a branded **PDF/Markdown** report (symptom,
  every check + result + photo, root cause, repair, verification, parts). Reuse `wiki/` export.
- **Auto-wiki.** Publish resolved cases to an internal wiki (Markdown pages per module/fault),
  searchable and feeding back into RAG. This is the compounding asset.

### Phase 5 — Knowledge ingestion at scale
- **Batch diagram ingestion (ProDemand etc.).** A pipeline + background workers to bulk-import
  PDFs for many modules: queue → extract (identity, tags, pinout, memories) → review. A CLI
  (`canopy vision ingest <dir>`) and a worker (Celery/RQ/arq) so 100s of PDFs process without
  blocking the UI. Human spot-check/confirm step preserved.
- **Curation.** Dedup/merge connectors and memories across the corpus; flag low-confidence
  extractions for review.

### Phase 6 — Bench fleet & "car in a box" integration
- **Per-tech benches.** Today `/api/can/*` drives the *server's* CAN interface. For many techs,
  run a small **bench agent** on each workstation/Pi (exposing its local USB-CAN + future matrix/
  power HAL), registered to the server; the UI routes bench commands to the tech's agent. This is
  the bridge to the [HARDWARE.md](HARDWARE.md) station and the simulator fleet.
- **Restbus + actuation library.** Per-module test routines (e.g. "command A/C clutch relay")
  built from the pinout + learned UDS/IO-control ids, runnable from the session.

### Phase 7 — Scale, reliability, ops
- Multi-worker (gunicorn/uvicorn workers) behind nginx; background job queue; model serving
  (Ollama on GPU, or a hosted fallback for burst); observability (logs/metrics/traces), backups,
  RBAC + audit log, rate limits. CI for the test suite already exists.

---

## Architecture target (sketch)

```
   Techs' browsers / phones                Bench agents (per workstation)
            │                                     │  USB-CAN + HAL
            ▼                                     ▼
   ┌──────────────────────── CANOPY service (nginx → app workers) ───────────────────────┐
   │  Auth/RBAC · Sessions · Projects/Modules · Repair-session engine · Reports/Wiki       │
   │  Vision (extract) · Assistant (RAG) · Research · Bench routing                         │
   └───────┬───────────────────────┬───────────────────────┬───────────────┬──────────────┘
           ▼                       ▼                       ▼               ▼
   Postgres + pgvector      Object storage (S3)      Job queue/workers   Ollama (GPU)
   (knowledge + vectors)    (diagrams, photos)       (ingest, extract)   / hosted models
```

---

## Guiding principles
- **Local-first, privacy-preserving by default** (proprietary service-manual content stays on
  the org's infra); cloud models optional per-deployment.
- **Human-in-the-loop, always.** The AI guides and aggregates; the tech decides and acts.
  Confirm-before-energize and confirm-before-publish stay sacred.
- **Every interaction compounds.** Each session makes the next one faster — that's the moat and
  the whole point.
- **Sourced, not hallucinated.** Research and answers cite where they came from so a tech can
  triage and trust.

---

## Near-term next steps (highest leverage first)
1. **Postgres + pgvector migration** of the vision store (unblocks org-wide semantic search +
   multi-user). 
2. **RepairSession object + guided-session UI** (the core workflow) with PCB-photo triage.
3. **Real accounts/roles** on top of today's cookie auth.
4. **Phone pairing** for real-time photo capture.
5. **Report/wiki export** from a session.
6. **Batch ProDemand ingestion** pipeline + worker.
