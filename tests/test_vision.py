"""Vision tool tests: store round-trip, JSON parsing, and extraction with a fake model.

No live model is contacted — a FakeClient returns canned responses so the extraction and
app wiring are tested deterministically and offline.
"""

from __future__ import annotations

from pathlib import Path

from canopy.vision.extract import (
    extract_pinout,
    identify_vehicle,
    parse_json_object,
    suggest_memories,
)
from canopy.vision.store import Store


class FakeClient:
    """Stands in for OllamaClient; returns a queued reply per call."""

    def __init__(self, reply: str):
        self.reply = reply
        self.calls: list[dict] = []

    def chat(self, messages, *, format_json=False, temperature=0.2, model=None) -> str:
        self.calls.append({"messages": messages, "format_json": format_json})
        return self.reply


def test_parse_json_object_handles_fences_and_prose() -> None:
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('sure!\n{"b": 2} done') == {"b": 2}
    assert parse_json_object("not json") == {}


def test_extract_pinout_normalizes() -> None:
    client = FakeClient(
        '{"connector":"C175","pins":[{"pin":1,"signal":"CAN-H"},{"pin":"2","signal":"CAN-L","wire_color":"green"}]}'
    )
    out = extract_pinout(client, images=["<b64>"])
    assert out["connector"] == "C175"
    assert out["pins"][0] == {
        "connector": "C175", "pin": "1", "signal": "CAN-H",
        "wire_color": "", "mating": "", "notes": "",
    }
    assert out["pins"][1]["wire_color"] == "green"
    assert client.calls[0]["format_json"] is False  # constrained JSON breaks some local models


def test_identify_and_suggest_memories() -> None:
    ident = identify_vehicle(FakeClient('{"vin":"1FT7W2BT0GEA12345","make":"Ford"}'), ["<b64>"])
    assert ident["vin"] == "1FT7W2BT0GEA12345"
    assert ident["model"] == ""

    mems = suggest_memories(FakeClient('{"memories":["CAN-H on pin 6","",  "PCM at C175"]}'), "x")
    assert mems == ["CAN-H on pin 6", "PCM at C175"]


def test_store_round_trip(tmp_path: Path) -> None:
    store = Store(tmp_path / "v.db")
    v = store.create_vehicle(vin="1FT7W2BT0GEA12345", make="Ford", model="F-250 6.7L")
    assert v["id"]

    store.add_diagram(v["id"], filename="c175.png", path="/tmp/c175.png", mime="image/png")
    d = store.latest_diagram(v["id"])
    assert d["filename"] == "c175.png"

    store.replace_pinouts(v["id"], d["id"], [
        {"connector": "C175", "pin": "6", "signal": "CAN-H"},
        {"connector": "C175", "pin": "14", "signal": "CAN-L"},
    ])
    pins = store.list_pinouts(v["id"])
    assert {p["signal"] for p in pins} == {"CAN-H", "CAN-L"}

    store.add_memory(v["id"], "CAN bus is HS-CAN at 500k", kind="learned")
    assert store.list_memories(v["id"])[0]["kind"] == "learned"

    store.add_message(v["id"], "user", "how do I wire CAN?")
    store.add_message(v["id"], "assistant", "Connect pin 6 to CAN-H…")
    assert len(store.list_messages(v["id"])) == 2

    store.delete_vehicle(v["id"])
    assert store.list_vehicles() == []
    store.close()
