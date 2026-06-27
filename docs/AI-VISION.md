# CANOPY — Local AI Wiring-Diagram Tool

A self-hosted web app that reads an automotive **wiring-diagram screenshot or PDF** with a
**local multimodal LLM (via Ollama)**, extracts the connector pinout, drafts a **CAN bench
wiring plan**, and lets you **chat about the diagram** and **save per-vehicle memories**
(keyed by VIN). Everything runs on your machine — **no diagram or VIN ever leaves it.**

This implements the human-in-the-loop vision pipeline from [CLAUDE.md](../CLAUDE.md) §7.3,
including the **confirm-before-energize** discipline: the AI proposes, the tech verifies.

---

## What it does

- **Ingest** an image (PNG/JPG) or a **multi-page PDF** wiring diagram. You navigate
  page-by-page; each page is usually one connector view.
- **Extract pinout** → for the page you’re on (or **all pages** at once). For PDFs the tool
  feeds the model both the page image **and its embedded text layer** (authoritative for pin
  numbers, signal labels, and wire codes), so pins map accurately. Results accumulate across
  pages, upserted by connector + pin.
- **Click any pin** → a detail panel shows its **function** in plain language, plus circuit
  id, wire color, what it connects to, and the source page. CAN / power / ground pins are
  color-coded.
- **Identify vehicle** → pulls VIN / year / make / model from the diagram when printed.
- **CAN wiring plan** → a step-by-step plan mapping module pins to station resources (KL30,
  KL15, GND, CAN-H, CAN-L), always led by a safety block.
- **Chat** → ask things like *“How do I wire this to communicate over CAN?”* or *“How can I
  simulate a test on the A/C clutch relay in this vehicle?”* The model sees the current page,
  its text, and the vehicle’s saved facts + accumulated pinout.
- **Memories** → save durable, vehicle-specific knowledge (manually, or auto-extracted from
  a chat answer). Accumulates a per-vehicle knowledge base over time.

### Example (2016 F-250 6.7L service diagram)
On the CAN page the tool correctly extracts `pin 59 → HS CAN + (CAN High)`,
`pin 43 → HS CAN - (CAN Low)`, and `pin 02 → ACCR (A/C clutch relay control →
Manual Climate Control System)` — each clickable for its full function, circuit, and color.

---

## Prerequisites

1. **Ollama** running locally (`http://localhost:11434`). Check: `ollama list`.
2. A **multimodal** model pulled. Default is **`gemma4:26b`** (what this machine uses).
   Good alternatives: `gemma3:27b`, `gemma3:12b` (all vision-capable).
   ```bash
   ollama pull gemma4:26b      # or gemma3:27b / gemma3:12b
   ```
3. The CANOPY **vision extra**:
   ```bash
   pip install -e ".[vision]"
   ```

---

## Run it

```bash
canopy vision serve                      # → http://127.0.0.1:8088
canopy vision serve --port 9000 --model gemma3:27b
```

Open the URL in a browser. The status pill (top-right) turns green when the model is ready.

> First request loads the model into memory and can take 30–90 s for a 17 GB model;
> subsequent requests are fast.

---

## Workflow

### Fast path — upload & auto-analyze
1. **+** in the sidebar creates a project; drop a diagram on the **Diagram** panel.
2. On upload the AI makes a **first attempt** at identity (year/make/model/engine/**module
   type**), a **project name**, and **tags**, then opens a **confirmation modal**.
3. Edit anything, choose what to auto-run (extract **pinout**, **CAN plan**, **memories**),
   and hit **Confirm & extract** — the project is named, tagged, and populated automatically.

Manage projects right from the sidebar: **rename** and **delete** buttons appear on hover; **+** adds.

### Manual path
1. **+ New project** → it appears in the sidebar.
2. **Drop a wiring-diagram** image or PDF onto the diagram panel.
3. **Navigate** with ◀ ▶ (or type a page number) to the page showing the connector you want.
4. **Extract this page** → pins appear, grouped by connector. Or **Extract all pages** to
   scan the whole document (slower — one model pass per page).
5. **Click any pin** → see its function, circuit, color, destination, and source page.
6. **Identify from diagram** → auto-fills VIN/year/make/model when present; edit + **Save**.
7. **CAN wiring plan** → generates a connection plan + safety block from the saved pinout.
8. **Chat** → use a suggested chip or type your own question. Toggle *“Save learned facts to
   memory”* to let the model distill durable facts after each answer.
9. **Memories** → add your own, or review/delete what was saved. These feed back into every
   future chat for that vehicle.

---

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CANOPY_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `CANOPY_OLLAMA_MODEL` | `gemma4:26b` | Multimodal model name |
| `CANOPY_OLLAMA_TIMEOUT` | `600` | Per-request timeout (seconds) |
| `CANOPY_VISION_DATA` | `~/.canopy/vision` | SQLite DB + uploaded diagrams |

CLI flags (`--model`, `--ollama-url`, `--host`, `--port`) override the environment.

---

## Where data lives

- **Database:** `~/.canopy/vision/canopy_vision.db` (SQLite) — vehicles, pinouts, memories,
  chat history.
- **Uploaded diagrams:** `~/.canopy/vision/uploads/`.

To reset, stop the server and delete the data directory. To back up a vehicle’s knowledge,
copy the SQLite file.

---

## Interface

The UI is a **VS Code-style dockable workspace**:

- **Drag any tab** (Diagram · Pinout · Wiring Plan · Chat · Memories · Record · API) to a
  panel's edge (left/right/top/bottom) to **split**, or onto another panel's tab bar to
  move it there. **Drag the borders** between panels to **resize** (e.g. PDF 60% / pinout
  40%). Close a tab with its ✕; re-add via the **+** on any tab bar. Layout is remembered.
- **PDF zoom** (− / % / + / fit) and page navigation in the Diagram panel.
- **Floating pin filter + sticky detail** in the Pinout panel (minimal scrolling). Click a
  pin to jump the Diagram to that pin's page.
- **Projects** in the sidebar: search by title/tag, sort by recent/title, group by make or
  year. Each project carries **tags** (added by hand or **AI-extracted** from the diagram).
- **Hover-able pin references** in the plan/chat (function + page), **light/dark theme**,
  **streaming** chat, and an in-app **API** tab with copy-paste examples (also `/api/docs`).

### Smarter memory (embeddings)

Memories are embedded with **`nomic-embed-text`**. New facts are saved only if they're
**semantically distinct** from existing ones (no duplicate restatements), and chat pulls
the **most relevant** memories (not just the most recent) into context — which improves
answers to abstract questions.

## Notes & limitations

- **Verify before you energize.** Vision parses can be wrong. Every CAN plan and answer
  reminds you to confirm power/ground pins with a meter and set the PSU current limit first.
  The station never auto-energizes from an AI parse (CLAUDE.md §10).
- **Model choice matters.** Pinout extraction uses prompt-driven JSON (not Ollama’s
  constrained `format=json`), because constrained decoding makes some local models —
  including `gemma4` — degenerate into repetition loops. If a model returns empty/garbled
  pinouts, try `gemma3:27b` or `gemma3:12b`.
- **Diagram quality matters.** Higher-resolution, legible connector tables extract best.
  Large images are auto-downscaled to ~2000 px on the long edge for responsiveness.
- **Local only.** No cloud calls; safe for proprietary service-manual material.

---

## How it fits the bigger picture

Today this is a standalone copilot. Next steps wire it into the rest of CANOPY:
- Emit a **draft module profile** (YAML) + **switch-matrix routing** from the extracted
  pinout (Phase 4), behind the confirm-before-energize gate.
- Cross-reference the pinout against the **vehicle simulator** so “simulate the A/C clutch
  relay” becomes an actual restbus + actuation sequence on the bench.
- Use `nomic-embed-text` (already installed) to make memories **semantically searchable**
  across vehicles.
