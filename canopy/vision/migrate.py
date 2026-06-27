"""Migrate the vision knowledge base from local SQLite into Postgres + pgvector.

Copies every project (vehicle) and its diagrams, pinouts, tags, memories (with embeddings),
chat/triage transcripts, and attachments. Idempotent-ish: it appends, so run it once into a
fresh Postgres DB. New ids are assigned in Postgres; relationships are preserved per-project.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from canopy.vision.pgstore import PgStore
from canopy.vision.store import Store

CHANNELS = ("chat", "triage")


def migrate_sqlite_to_pg(sqlite_path: str | Path, pg_url: str,
                         *, log: Callable[[str], None] = print) -> dict:
    src = Store(Path(sqlite_path))
    dst = PgStore(pg_url)
    counts = {k: 0 for k in
              ("projects", "diagrams", "pinouts", "memories", "tags", "messages", "attachments")}
    try:
        for v in src.list_vehicles():
            nv = dst.create_vehicle(vin=v.get("vin", ""), year=v.get("year", ""),
                                    make=v.get("make", ""), model=v.get("model", ""),
                                    label=v.get("label", ""))
            vid, old = nv["id"], v["id"]
            counts["projects"] += 1

            for t in src.list_tags(old):
                dst.add_tag(vid, t)
                counts["tags"] += 1

            dmap: dict[int, int] = {}
            for d in src.list_diagrams(old):
                nd = dst.add_diagram(vid, filename=d.get("filename", ""), path=d.get("path", ""),
                                     mime=d.get("mime", ""), pages=d.get("pages", 1))
                dmap[d["id"]] = nd["id"]
                counts["diagrams"] += 1

            for p in src.list_pinouts(old):
                dst.merge_pinouts(vid, dmap.get(p.get("diagram_id")), p.get("page"), [p])
                counts["pinouts"] += 1

            for m in src.list_memories(old):
                dst.add_memory(vid, m["content"], kind=m.get("kind", "note"),
                               embedding=m.get("embedding"))
                counts["memories"] += 1

            for ch in CHANNELS:
                for msg in src.list_messages(old, limit=10000, channel=ch):
                    dst.add_message(vid, msg["role"], msg["content"], channel=ch)
                    counts["messages"] += 1

            for a in src.list_attachments(old):
                dst.add_attachment(vid, a["path"], kind=a.get("kind", "photo"),
                                   note=a.get("note", ""))
                counts["attachments"] += 1

            log(f"  migrated project '{nv['label'] or vid}' (was {old})")
    finally:
        src.close()
        dst.close()
    return counts
