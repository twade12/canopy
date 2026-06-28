"""Compile a project's accumulated knowledge into a single shareable Markdown wiki page.

Pulls together everything CANOPY has learned about a module — identity, connector pinout, the
boxed/identified (and tech-corrected) board components, annotated images, and accumulated
failure-mode notes — into one document a technician can read, copy into the team wiki, or print.
Images are embedded as server-relative URLs so they render in-app and on the same host.
"""

from __future__ import annotations


def _esc(s: object) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def build(store, vehicle_id: int) -> str:
    v = store.get_vehicle(vehicle_id)
    ident = " ".join(filter(None, [v.get("year"), v.get("make"), v.get("model")]))
    title = v.get("label") or ident or "Module"
    out: list[str] = [f"# {title} — repair wiki", ""]

    meta = []
    if ident:
        meta.append(f"**Module:** {ident}")
    if v.get("vin"):
        meta.append(f"**VIN:** {v['vin']}")
    tags = store.list_tags(vehicle_id)
    if tags:
        meta.append(f"**Tags:** {', '.join(tags)}")
    if meta:
        out += ["  ·  ".join(meta), ""]

    pins = store.list_pinouts(vehicle_id)
    if pins:
        out += ["## Connector pinout", "",
                "| Connector | Pin | Signal | Function | Wire | Notes |",
                "|---|---|---|---|---|---|"]
        for p in pins:
            out.append("| " + " | ".join(_esc(p.get(k, "")) for k in
                       ("connector", "pin", "signal", "function", "wire_color", "notes")) + " |")
        out.append("")

    comps = store.list_pcb_components(vehicle_id)
    if comps:
        out += ["## Board components", ""]
        for c in comps:
            name = c.get("user_label") or c.get("label") or "component"
            part = f" (`{c['part']}`)" if c.get("part") else ""
            edited = " — **tech-verified**" if c.get("user_label") else ""
            out.append(f"- **{name}**{part}{edited} — {c.get('function', '')}".rstrip(" —"))
            if c.get("check"):
                out.append(f"  - Check: {c['check']}")
            if c.get("user_note"):
                out.append(f"  - Note: {c['user_note']}")
        out.append("")

    annos = [a for a in store.list_attachments(vehicle_id) if a.get("kind") == "annotation"]
    if annos:
        out += ["## Annotated images", ""]
        for a in annos:
            if a.get("note"):
                out.append(f"*{a['note']}*")
            out += [f"![annotation](/api/attachment/{a['id']}/image)", ""]

    meas = store.list_measurements(vehicle_id)
    if meas:
        out += ["## Recorded measurements", ""]
        dmm = [m for m in meas if m.get("kind") == "dmm"]
        if dmm:
            out += ["| When | Measurement | Reading |", "|---|---|---|"]
            for m in dmm:
                when = str(m.get("created_at", ""))[:16]
                val = f"{m.get('value')} {m.get('unit', '')}".strip()
                out.append(f"| {when} | {_esc(m.get('label') or m.get('mode'))} | {val} |")
            out.append("")
        for m in meas:
            if m.get("kind") == "scope" and m.get("attachment_id"):
                if m.get("label"):
                    out.append(f"*{m['label']}*")
                out += [f"![scope capture](/api/attachment/{m['attachment_id']}/image)", ""]

    mems = store.list_memories(vehicle_id)
    if mems:
        out += ["## Known failure modes & accumulated notes", ""]
        out += [f"- {m['content']}" for m in mems]
        out.append("")

    out += ["---",
            "**Diagnose with the CANOPY field methodology:** power-up order, divide-and-conquer, "
            "verify-then-repair. Reason from this pinout — never from invented values."]
    return "\n".join(out)
