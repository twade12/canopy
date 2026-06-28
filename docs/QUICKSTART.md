# Canopy quick start (for new users)

Canopy turns a module's wiring diagram and board photos into grounded triage, documented repairs,
and a CAB-ready test profile. This is the 5-minute tour. (Architecture: `CLAUDE.md`. Bench plan:
`docs/CAB-INTEGRATION.md`.)

## The shape of it
- **Left sidebar = Projects.** One project per module/job (a make/model/year + its module). Create
  with **+**, search/sort/group, rename, delete. Each tab below works on the *selected* project.
- **Workspace = dockable tabs.** Drag tabs to rearrange, split, or pop into columns; the **+** on a
  tab strip adds a panel; the **⤢** maximizes a panel. Each browser tab remembers its own layout and
  project, and the browser title shows the project.
- The **toast** (top-right) streams what the AI is doing; click **Stop** to cancel.

## A typical first pass
1. **Create a project** (+), then drag a **wiring diagram** (image or PDF) onto the **Diagram** tab.
2. **Pinout** → *Extract* reads the connector pinout from the diagram (schematic-aware). Hover a pin
   for its function; click a pin reference anywhere to jump the diagram to that page.
3. **PCB** → drop a board photo (or pair your phone). Canopy boxes and identifies the components
   (reading part markings), tells you what to check on each, and lets you **Edit boxes** (drag/
   resize/add/delete) and **correct** any it gets wrong. Multiple photos per project.
4. **Guided** → the star for newcomers: enter the customer symptom and step through a physics-first
   walkthrough (Intake → Sealed checks → Power-up → Open & inspect → Board checks → Root cause →
   Document). It reasons out loud, recommends the single simplest next check (why / how / tool /
   expected / record / safety), you log Pass/Fail, and it adapts.
5. **Triage** → free-form expert chat (same grounded engine) when you want to drive the conversation.
6. **Profile** → auto-drafts the **CAB test profile** from the pinout/PCB: identity, CAB cards, the
   harness map (pin → role → CAB card/channel), and safety gates. Review, **Save / confirm**, and
   **Download .yaml**. This is what plugs the module into the CAB bench. *Confirm before energizing.*
7. **Wiki** → compiles everything (pinout, components + corrections, annotated photos, notes) into
   one shareable page — Copy Markdown or Print/PDF.

## The other tabs
- **Memories** — salient facts Canopy retains per project; they're retrieved across projects to make
  the next similar module faster.
- **Knowledge** (topbar book icon) — the house EE/PCB troubleshooting knowledge base the AI consults
  during triage; searchable so you can read it too.
- **Bench** — connect a USB-to-CAN adapter (or `vcan0`) to monitor the bus, send frames, and run UDS
  (DTC read, etc.) against a live module.
- **Record** — the project's identity (make/model/year/VIN/part number) and tags.
- **Assistant** — cross-project Q&A over everything Canopy has learned.
- **Research** — web research to fill gaps (harness images, pin layouts) with cited sources.
- **API** — the REST API reference for automation.

## Phone capture
On **PCB** or **Triage**, click **Pair phone** → scan the QR with a phone on the same Wi-Fi/VPN.
Photos appear in the dialog within ~1–2 s; tap **PCB** to analyze the board or **Triage** to attach.

## Good habits
- Reason from the real pinout and what you measure — Canopy is built to *not* invent values.
- Correct the AI when it's wrong (PCB labels, memories); those corrections compound.
- Confirm power/ground/CAN pins before energizing anything.
