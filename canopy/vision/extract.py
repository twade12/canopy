"""Structured extraction + advice built on the Ollama client and prompts.

Each function takes a client and base64 image(s) and returns parsed results. JSON parsing
is defensive: local models sometimes wrap JSON in prose or code fences.
"""

from __future__ import annotations

import json
import re

from canopy.vision.ollama_client import ChatMessage, OllamaClient
from canopy.vision.prompts import (
    CAN_PLAN_SYSTEM,
    CHAT_SYSTEM,
    EXTRACT_SYSTEM,
    IDENTIFY_SYSTEM,
    MEMORY_SUGGEST_SYSTEM,
)


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
    return {k: str(data.get(k, "")) for k in ("vin", "year", "make", "model", "notes")}


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
