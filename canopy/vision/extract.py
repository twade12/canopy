"""Structured extraction + advice built on the Ollama client and prompts.

Each function takes a client and base64 image(s) and returns parsed results. JSON parsing
is defensive: local models sometimes wrap JSON in prose or code fences.
"""

from __future__ import annotations

import json
import math
import re

from canopy.vision.ollama_client import ChatMessage, OllamaClient
from canopy.vision.prompts import (
    ASSISTANT_SYSTEM,
    CAN_PLAN_SYSTEM,
    CHAT_SYSTEM,
    COMPONENT_IDENTIFY_SYSTEM,
    EXTRACT_SYSTEM,
    GUIDED_SYSTEM,
    IDENTIFY_SYSTEM,
    MEMORY_SUGGEST_SYSTEM,
    PCB_SYSTEM,
    REPORT_SYSTEM,
    TAGS_SYSTEM,
    TRIAGE_SYSTEM,
)


def analyze_pcb(client: OllamaClient, images: list[str], context: str = "") -> dict:
    """Identify PCB components with bounding boxes (fractions 0..1) + function/check/tool."""
    user = ("Identify and box EVERY component you can see on this board. Read the printed part "
            "numbers/markings on the chips and parts and use them to identify each one. Work "
            "across the whole board corner to corner — include the small passives, diodes, and "
            "transistors, not just the big ICs.")
    if context:
        user += f"\n\nThis module's identity and pinout (use to ground your analysis):\n{context}"
    messages = [
        ChatMessage("system", PCB_SYSTEM),
        ChatMessage("user", user, images=images),
    ]
    data = parse_json_object(client.chat(messages, temperature=0.0))
    raw = []
    for c in data.get("components", []) or []:
        if not isinstance(c, dict):
            continue
        box = c.get("box") or []
        if not (isinstance(box, list) and len(box) == 4):
            continue
        try:
            raw.append((c, [float(x) for x in box]))
        except (TypeError, ValueError):
            continue
    if not raw:
        return {"components": []}
    # gemma/Gemini emit boxes as [ymin, xmin, ymax, xmax] on a 0-1000 scale. Auto-detect
    # 0-1000 vs 0..1 fractions, then convert to fractional [x0, y0, x1, y1].
    mx = max(v for _, vals in raw for v in vals)
    scale = 1000.0 if mx > 1.5 else 1.0

    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    comps = []
    for c, vals in raw:
        ymin, xmin, ymax, xmax = (v / scale for v in vals)
        x0, x1 = sorted((xmin, xmax))
        y0, y1 = sorted((ymin, ymax))
        comps.append({
            "label": str(c.get("label", "")),
            "box": [clamp(x0), clamp(y0), clamp(x1), clamp(y1)],
            "function": str(c.get("function", "")),
            "check": str(c.get("check", "")),
            "part": str(c.get("part", "")),
            "confidence": float(c.get("confidence", 0) or 0),
        })
    return {"components": comps}


def identify_component(client: OllamaClient, label: str, part: str = "", context: str = "") -> dict:
    """Given a (newly drawn) component's name + optional marking, return its function + what to
    check — the same metadata the bulk PCB analysis produces, for boxes the tech adds by hand."""
    user = f"Component: {label}\nPart marking: {part or '(none)'}"
    if context:
        user += f"\n\nModule identity & pinout (ground your answer in this):\n{context}"
    messages = [
        ChatMessage("system", COMPONENT_IDENTIFY_SYSTEM),
        ChatMessage("user", user),
    ]
    data = parse_json_object(client.chat(messages, temperature=0.1))
    return {"function": str(data.get("function", "")), "check": str(data.get("check", ""))}


def guided_next(client: OllamaClient, *, context: str, phase: str, symptom: str, log: str) -> dict:
    """Recommend the single next guided-repair step as structured JSON (see GUIDED_SYSTEM)."""
    user = (f"CURRENT PHASE: {phase}\nSYMPTOM: {symptom or '(not stated yet)'}\n\n"
            f"STEPS DONE SO FAR (with results):\n{log or '(none yet)'}\n\n"
            f"MODULE + KNOWLEDGE:\n{context}\n\nGive the next step as JSON.")
    messages = [ChatMessage("system", GUIDED_SYSTEM), ChatMessage("user", user)]
    data = parse_json_object(client.chat(messages, temperature=0.2))
    return {
        "title": str(data.get("title", "")),
        "why": str(data.get("why", "")),
        "how": str(data.get("how", "")),
        "tool": str(data.get("tool", "")),
        "expected": str(data.get("expected", "")),
        "record": str(data.get("record", "")),
        "safety": str(data.get("safety", "")),
        "phase_complete": bool(data.get("phase_complete", False)),
        "next_phase": str(data.get("next_phase", phase) or phase),
        "done": bool(data.get("done", False)),
        "root_cause": str(data.get("root_cause", "")),
        "repair": str(data.get("repair", "")),
    }


def assistant_stream(client: OllamaClient, question: str, *, context: str, history: list):
    """Stream a global cross-vehicle assistant answer (no diagram image)."""
    messages = [ChatMessage("system", ASSISTANT_SYSTEM + "\n\n" + context)]
    messages.extend(history)
    messages.append(ChatMessage("user", question))
    yield from client.chat_stream(messages, temperature=0.3)


def triage_stream(client: OllamaClient, message: str, *, context: str, history: list,
                  images: list[str]):
    """Stream a guided repair-triage answer (multimodal: may include a board/scope photo)."""
    messages = [ChatMessage("system", TRIAGE_SYSTEM + "\n\n" + context)]
    messages.extend(history)
    messages.append(ChatMessage("user", message, images=images))
    yield from client.chat_stream(messages, temperature=0.3)


def repair_report(client: OllamaClient, transcript: str, facts: str) -> str:
    """Compile a triage transcript + module facts into a Markdown repair report."""
    messages = [
        ChatMessage("system", REPORT_SYSTEM),
        ChatMessage("user", f"MODULE FACTS:\n{facts}\n\nTRIAGE TRANSCRIPT:\n{transcript}"),
    ]
    return client.chat(messages, temperature=0.2)


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors (0 if either is empty/zero)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def is_novel(vec: list[float], existing: list[list[float]], *, threshold: float = 0.86) -> bool:
    """True if `vec` is not near-duplicate of any existing embedding."""
    return all(cosine(vec, e) < threshold for e in existing if e)


def rank_by_similarity(query: list[float], items: list[tuple], *, k: int = 6) -> list:
    """Sort (vector, payload) items by cosine to `query`; return top-k payloads."""
    scored = [(cosine(query, vec), payload) for vec, payload in items if vec]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [payload for _, payload in scored[:k]]


def extract_tags(client: OllamaClient, images: list[str], identity: str = "") -> list[str]:
    """Extract short searchable tags (make, model, year, system, module type)."""
    user = "Extract tags for this project."
    if identity:
        user += f"\nKnown so far: {identity}"
    messages = [ChatMessage("system", TAGS_SYSTEM), ChatMessage("user", user, images=images)]
    data = parse_json_object(client.chat(messages, temperature=0.0))
    out, seen = [], set()
    for t in data.get("tags", []) or []:
        t = str(t).strip()
        key = t.lower()
        if t and key not in seen:
            seen.add(key)
            out.append(t)
    return out


def parse_json_object(text: str) -> dict:
    """Best-effort parse of a JSON object from possibly-noisy model output."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the first balanced-looking {...} span.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _coerce_pin(connector: str, p: dict) -> dict:
    return {
        "connector": connector,
        "pin": str(p.get("pin", "")),
        "signal": str(p.get("signal", "")),
        "function": str(p.get("function", "")),
        "wire_color": str(p.get("wire_color", "")),
        "circuit": str(p.get("circuit", "")),
        "connects_to": str(p.get("connects_to", "")),
        "mating": str(p.get("mating", "")),
        "notes": str(p.get("notes", "")),
    }


def extract_pinout(client: OllamaClient, images: list[str], page_text: str = "") -> dict:
    """Extract pins for the connector(s) on one page.

    Returns ``{"connectors": [str], "pins": [ {connector, pin, signal, function, …} ]}``.
    The embedded ``page_text`` (PDF text layer) is authoritative and is sent alongside the
    image for accuracy.
    """
    user = "Extract every pin for the connector(s) on this diagram page."
    if page_text:
        user += (
            "\n\nThe page's extracted TEXT LAYER (authoritative for pin numbers, signal "
            f"labels, and wire codes) is below:\n---\n{page_text}\n---"
        )
    messages = [
        ChatMessage("system", EXTRACT_SYSTEM),
        ChatMessage("user", user, images=images),
    ]
    # Note: Ollama's constrained `format=json` makes some models (e.g. gemma4) degenerate
    # into repetition loops; prompt-driven JSON + defensive parsing is more reliable.
    data = parse_json_object(client.chat(messages, temperature=0.0))

    connectors_out: list[str] = []
    pins: list[dict] = []
    connectors = data.get("connectors")
    if isinstance(connectors, list) and connectors:
        for c in connectors:
            if not isinstance(c, dict):
                continue
            name = str(c.get("connector", ""))
            connectors_out.append(name)
            for p in c.get("pins", []) or []:
                if isinstance(p, dict):
                    pins.append(_coerce_pin(name, p))
    else:
        # Fallback: model returned the older flat shape.
        name = str(data.get("connector", ""))
        connectors_out.append(name)
        for p in data.get("pins", []) or []:
            if isinstance(p, dict):
                pins.append(_coerce_pin(name, p))
    return {"connectors": [c for c in connectors_out if c], "pins": pins}


def identify_vehicle(client: OllamaClient, images: list[str]) -> dict:
    """Return ``{vin, year, make, model, notes}`` read from the diagram (blank if unknown)."""
    messages = [
        ChatMessage("system", IDENTIFY_SYSTEM),
        ChatMessage("user", "Identify the vehicle from this diagram.", images=images),
    ]
    data = parse_json_object(client.chat(messages, temperature=0.0))
    keys = ("vin", "year", "make", "model", "engine", "module_type", "notes")
    return {k: str(data.get(k, "")) for k in keys}


def can_bench_plan(client: OllamaClient, pinout_text: str, images: list[str]) -> str:
    """Return a Markdown CAN bench-connection plan for the given pinout."""
    prompt = f"Module pinout:\n{pinout_text}\n\nGive the CAN bench wiring plan."
    messages = [
        ChatMessage("system", CAN_PLAN_SYSTEM),
        ChatMessage("user", prompt, images=images),
    ]
    return client.chat(messages, temperature=0.2)


def chat_about_diagram(
    client: OllamaClient,
    question: str,
    *,
    context: str,
    history: list[ChatMessage],
    images: list[str],
) -> str:
    """Answer a question about the diagram, with saved context + recent history + image."""
    messages: list[ChatMessage] = [ChatMessage("system", CHAT_SYSTEM + "\n\n" + context)]
    messages.extend(history)
    messages.append(ChatMessage("user", question, images=images))
    return client.chat(messages, temperature=0.3)


def chat_about_diagram_stream(
    client: OllamaClient,
    question: str,
    *,
    context: str,
    history: list[ChatMessage],
    images: list[str],
):
    """Stream a chat answer token-by-token (for live 'thinking' in the UI)."""
    messages: list[ChatMessage] = [ChatMessage("system", CHAT_SYSTEM + "\n\n" + context)]
    messages.extend(history)
    messages.append(ChatMessage("user", question, images=images))
    yield from client.chat_stream(messages, temperature=0.3)


def dedup_memories(
    candidates: list[str], existing: list[str], *, threshold: float = 0.72
) -> list[str]:
    """Keep only candidates that are salient and not too similar to existing/each other."""
    import difflib

    def similar(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

    kept: list[str] = []
    pool = list(existing)
    for c in candidates:
        c = c.strip()
        if len(c) < 12:  # too trivial to be salient
            continue
        if any(similar(c, e) >= threshold for e in pool):
            continue
        kept.append(c)
        pool.append(c)
    return kept


def suggest_memories(client: OllamaClient, transcript: str) -> list[str]:
    """Propose durable vehicle facts worth saving from a transcript."""
    messages = [
        ChatMessage("system", MEMORY_SUGGEST_SYSTEM),
        ChatMessage("user", transcript),
    ]
    data = parse_json_object(client.chat(messages, temperature=0.0))
    return [str(m) for m in data.get("memories", []) or [] if str(m).strip()]
