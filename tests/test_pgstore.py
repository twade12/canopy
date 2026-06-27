"""PgStore integration test — runs only if CANOPY_TEST_DATABASE_URL points at a pgvector DB.

    docker run -d -e POSTGRES_PASSWORD=canopy -e POSTGRES_USER=canopy -e POSTGRES_DB=canopy \
        -p 5433:5432 pgvector/pgvector:pg16
    CANOPY_TEST_DATABASE_URL=postgresql://canopy:canopy@localhost:5433/canopy \
        pytest tests/test_pgstore.py
"""

from __future__ import annotations

import os

import pytest

DSN = os.environ.get("CANOPY_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="set CANOPY_TEST_DATABASE_URL to run")


@pytest.fixture
def store():
    from canopy.vision.pgstore import PgStore

    s = PgStore(DSN)
    for v in s.list_vehicles():  # clean slate
        s.delete_vehicle(v["id"])
    yield s
    s.close()


def test_pgstore_full_surface(store) -> None:
    v = store.create_vehicle(label="Rig", make="Chevrolet", model="Silverado")
    store.add_tag(v["id"], "Chevy")
    store.add_tag(v["id"], "chevy")                       # case-insensitive dedup
    assert store.list_tags(v["id"]) == ["Chevy"]
    assert store.list_vehicles()[0]["tags"] == ["Chevy"]

    d = store.add_diagram(v["id"], filename="x.pdf", path="/tmp/x.pdf", mime="application/pdf")
    store.merge_pinouts(v["id"], d["id"], 0, [
        {"connector": "1232b", "pin": "6", "signal": "CAN-H"},
        {"connector": "C1232B", "pin": "14", "signal": "CAN-L"},
    ])
    assert {p["connector"] for p in store.list_pinouts(v["id"])} == {"C1232B"}

    m = store.add_memory(v["id"], "Pin 6 is CAN-H", kind="learned", embedding=[0.1, 0.2, 0.3])
    assert m["embedding"] == [pytest.approx(0.1), pytest.approx(0.2), pytest.approx(0.3)]
    assert store.all_memories()[0]["project"] == "Rig"

    store.add_message(v["id"], "user", "hi", channel="triage")
    assert len(store.list_messages(v["id"], channel="triage")) == 1
    assert len(store.list_messages(v["id"])) == 0          # different channel

    store.add_attachment(v["id"], "/tmp/b.png", kind="photo")
    assert len(store.list_attachments(v["id"])) == 1

    store.delete_vehicle(v["id"])
    assert store.list_vehicles() == []
