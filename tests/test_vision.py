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


def test_extract_pinout_connectors_schema() -> None:
    client = FakeClient(
        '{"connectors":[{"connector":"C1232B","pins":['
        '{"pin":59,"signal":"HS CAN +","function":"CAN High","circuit":"VDB04",'
        '"wire_color":"WH/bu","connects_to":"Module Communication Network"}]}]}'
    )
    out = extract_pinout(client, ["<b64>"], page_text="59 HS CAN +")
    assert out["connectors"] == ["C1232B"]
    p = out["pins"][0]
    assert p["connector"] == "C1232B" and p["pin"] == "59"
    assert p["function"] == "CAN High" and p["circuit"] == "VDB04"
    assert p["connects_to"] == "Module Communication Network"
    assert client.calls[0]["format_json"] is False  # constrained JSON breaks some local models


def test_extract_pinout_flat_fallback() -> None:
    client = FakeClient('{"connector":"C175","pins":[{"pin":"6","signal":"CAN-H"}]}')
    out = extract_pinout(client, ["<b64>"])
    assert out["pins"][0]["pin"] == "6"
    assert out["pins"][0]["connector"] == "C175"


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

    # merge accumulates across pages and upserts by (connector, pin)
    store.merge_pinouts(v["id"], d["id"], 5, [
        {"connector": "C1232B", "pin": "59", "signal": "HS CAN +", "function": "CAN High",
         "circuit": "VDB04", "wire_color": "WH/bu"},
        {"connector": "C1232B", "pin": "43", "signal": "HS CAN -", "function": "CAN Low"},
    ])
    store.merge_pinouts(v["id"], d["id"], 6, [
        {"connector": "C1232B", "pin": "02", "signal": "ACCR", "function": "A/C clutch relay"},
        {"connector": "C1232B", "pin": "59", "signal": "HS CAN +", "function": "updated"},  # upsert
    ])
    pins = store.list_pinouts(v["id"])
    assert {p["pin"] for p in pins} == {"59", "43", "02"}   # 59 upserted, not duplicated
    by_pin = {p["pin"]: p for p in pins}
    assert by_pin["59"]["function"] == "updated"
    assert by_pin["02"]["function"] == "A/C clutch relay"
    assert by_pin["59"]["circuit"] == ""                    # row replaced; circuit not re-supplied

    store.add_memory(v["id"], "CAN bus is HS-CAN at 500k", kind="learned")
    assert store.list_memories(v["id"])[0]["kind"] == "learned"

    store.add_message(v["id"], "user", "how do I wire CAN?")
    store.add_message(v["id"], "assistant", "Connect pin 6 to CAN-H…")
    assert len(store.list_messages(v["id"])) == 2

    store.delete_vehicle(v["id"])
    assert store.list_vehicles() == []
    store.close()
