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


def extract_pinout(client: OllamaClient, images: list[str]) -> dict:
    """Return ``{"connector": str, "pins": [ {pin, signal, wire_color, mating, notes} ]}``."""
    messages = [
        ChatMessage("system", EXTRACT_SYSTEM),
        ChatMessage("user", "Extract the connector pinout from this diagram.", images=images),
    ]
    # Note: Ollama's constrained `format=json` makes some models (e.g. gemma4) degenerate
    # into repetition loops; prompt-driven JSON + defensive parsing is more reliable.
    data = parse_json_object(client.chat(messages, temperature=0.0))
    connector = str(data.get("connector", ""))
    pins = []
    for p in data.get("pins", []) or []:
        if not isinstance(p, dict):
            continue
        pins.append(
            {
                "connector": connector,
                "pin": str(p.get("pin", "")),
                "signal": str(p.get("signal", "")),
                "wire_color": str(p.get("wire_color", "")),
                "mating": str(p.get("mating", "")),
                "notes": str(p.get("notes", "")),
            }
        )
    return {"connector": connector, "pins": pins}


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


def suggest_memories(client: OllamaClient, transcript: str) -> list[str]:
    """Propose durable vehicle facts worth saving from a transcript."""
    messages = [
        ChatMessage("system", MEMORY_SUGGEST_SYSTEM),
        ChatMessage("user", transcript),
    ]
    data = parse_json_object(client.chat(messages, temperature=0.0))
    return [str(m) for m in data.get("memories", []) or [] if str(m).strip()]
