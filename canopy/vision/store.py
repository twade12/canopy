"""Local SQLite store for vehicles, diagrams, pinouts, memories, and chat.

Deliberately simple (stdlib ``sqlite3``, no ORM) and local-only — a tech's diagrams and
VINs never leave the machine. Knowledge is keyed by vehicle so the AI can answer
per-vehicle questions and accumulate memories over time.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def normalize_connector(name: str) -> str:
    """Canonicalize a connector label so '1232b' and 'C1232B' map to one key.

    Ford-style connector codes are an optional leading 'C', then digits, then an
    optional letter (e.g. C1232B). We always emit the leading-'C' uppercase form.
    Non-connector labels (e.g. 'PCM') pass through uppercased.
    """
    s = re.sub(r"\s+", "", str(name or "")).upper()
    m = re.fullmatch(r"C?(\d{2,}[A-Z]?)", s)
    return f"C{m.group(1)}" if m else s

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT, year TEXT, make TEXT, model TEXT, label TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS diagram (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    filename TEXT, path TEXT NOT NULL, mime TEXT, pages INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pinout (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    diagram_id INTEGER REFERENCES diagram(id) ON DELETE SET NULL,
    connector TEXT, pin TEXT, signal TEXT, function TEXT, wire_color TEXT,
    circuit TEXT, connects_to TEXT, mating TEXT, notes TEXT, page INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    kind TEXT DEFAULT 'note', content TEXT NOT NULL, embedding TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    role TEXT NOT NULL, content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Store:
    """A connection to the local vision database."""

    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """Add columns introduced after a DB was first created (lightweight migration)."""
        have = {r["name"] for r in self._conn.execute("PRAGMA table_info(pinout)")}
        for col in ("function TEXT", "circuit TEXT", "connects_to TEXT", "page INTEGER"):
            name = col.split()[0]
            if name not in have:
                self._conn.execute(f"ALTER TABLE pinout ADD COLUMN {col}")
        mem = {r["name"] for r in self._conn.execute("PRAGMA table_info(memory)")}
        if "embedding" not in mem:
            self._conn.execute("ALTER TABLE memory ADD COLUMN embedding TEXT")

    def close(self) -> None:
        self._conn.close()

    # --- vehicles --------------------------------------------------------------
    def create_vehicle(
        self, *, vin: str = "", year: str = "", make: str = "", model: str = "", label: str = ""
    ) -> dict:
        cur = self._conn.execute(
            "INSERT INTO vehicle (vin, year, make, model, label, created_at) VALUES (?,?,?,?,?,?)",
            (vin, year, make, model, label, _now()),
        )
        self._conn.commit()
        return self.get_vehicle(cur.lastrowid)

    def update_vehicle(self, vehicle_id: int, **fields) -> dict:
        allowed = {"vin", "year", "make", "model", "label"}
        sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if sets:
            assignments = ", ".join(f"{k} = ?" for k in sets)
            self._conn.execute(
                f"UPDATE vehicle SET {assignments} WHERE id = ?",
                (*sets.values(), vehicle_id),
            )
            self._conn.commit()
        return self.get_vehicle(vehicle_id)

    def get_vehicle(self, vehicle_id: int) -> dict:
        row = self._conn.execute("SELECT * FROM vehicle WHERE id = ?", (vehicle_id,)).fetchone()
        if row is None:
            raise KeyError(f"no vehicle {vehicle_id}")
        return dict(row)

    def list_vehicles(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM vehicle ORDER BY created_at DESC").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["tags"] = self.list_tags(d["id"])
            out.append(d)
        return out

    def delete_vehicle(self, vehicle_id: int) -> None:
        self._conn.execute("DELETE FROM vehicle WHERE id = ?", (vehicle_id,))
        self._conn.commit()

    # --- diagrams --------------------------------------------------------------
    def add_diagram(
        self, vehicle_id: int, *, filename: str, path: str, mime: str, pages: int = 1
    ) -> dict:
        cur = self._conn.execute(
            "INSERT INTO diagram (vehicle_id, filename, path, mime, pages, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (vehicle_id, filename, path, mime, pages, _now()),
        )
        self._conn.commit()
        return self.get_diagram(cur.lastrowid)

    def get_diagram(self, diagram_id: int) -> dict:
        row = self._conn.execute("SELECT * FROM diagram WHERE id = ?", (diagram_id,)).fetchone()
        if row is None:
            raise KeyError(f"no diagram {diagram_id}")
        return dict(row)

    def list_diagrams(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM diagram WHERE vehicle_id = ? ORDER BY created_at DESC", (vehicle_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def latest_diagram(self, vehicle_id: int) -> dict | None:
        rows = self.list_diagrams(vehicle_id)
        return rows[0] if rows else None

    # --- pinouts ---------------------------------------------------------------
    def _insert_pinout(
        self, vehicle_id: int, diagram_id: int | None, page: int | None, r: dict
    ) -> None:
        self._conn.execute(
            "INSERT INTO pinout (vehicle_id, diagram_id, connector, pin, signal, function,"
            " wire_color, circuit, connects_to, mating, notes, page, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                vehicle_id, diagram_id,
                str(r.get("connector", "")), str(r.get("pin", "")), str(r.get("signal", "")),
                str(r.get("function", "")), str(r.get("wire_color", "")), str(r.get("circuit", "")),
                str(r.get("connects_to", "")), str(r.get("mating", "")), str(r.get("notes", "")),
                page, _now(),
            ),
        )

    def merge_pinouts(
        self, vehicle_id: int, diagram_id: int | None, page: int | None, rows: list[dict]
    ) -> list[dict]:
        """Upsert rows by (connector, pin) so multi-page extraction accumulates."""
        for r in rows:
            pin = str(r.get("pin", ""))
            if not pin:
                continue
            r = {**r, "connector": normalize_connector(r.get("connector", ""))}
            self._conn.execute(
                "DELETE FROM pinout WHERE vehicle_id = ? AND connector = ? AND pin = ?",
                (vehicle_id, r["connector"], pin),
            )
            self._insert_pinout(vehicle_id, diagram_id, page, r)
        self._conn.commit()
        return self.list_pinouts(vehicle_id)

    def replace_pinouts(
        self, vehicle_id: int, diagram_id: int | None, rows: list[dict], page: int | None = None
    ) -> list[dict]:
        """Replace this vehicle's pinouts with a freshly extracted set."""
        self._conn.execute("DELETE FROM pinout WHERE vehicle_id = ?", (vehicle_id,))
        for r in rows:
            self._insert_pinout(vehicle_id, diagram_id, page, r)
        self._conn.commit()
        return self.list_pinouts(vehicle_id)

    def clear_pinouts(self, vehicle_id: int) -> None:
        self._conn.execute("DELETE FROM pinout WHERE vehicle_id = ?", (vehicle_id,))
        self._conn.commit()

    def list_pinouts(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM pinout WHERE vehicle_id = ?"
            " ORDER BY connector, CAST(pin AS INTEGER), pin",
            (vehicle_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- memories --------------------------------------------------------------
    def add_memory(
        self, vehicle_id: int, content: str, *, kind: str = "note", embedding: list | None = None
    ) -> dict:
        cur = self._conn.execute(
            "INSERT INTO memory (vehicle_id, kind, content, embedding, created_at)"
            " VALUES (?,?,?,?,?)",
            (vehicle_id, kind, content, json.dumps(embedding) if embedding else None, _now()),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM memory WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._memory_row(row)

    @staticmethod
    def _memory_row(row) -> dict:
        d = dict(row)
        d["embedding"] = json.loads(d["embedding"]) if d.get("embedding") else None
        return d

    def list_memories(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM memory WHERE vehicle_id = ? ORDER BY created_at DESC", (vehicle_id,)
        ).fetchall()
        return [self._memory_row(r) for r in rows]

    def delete_memory(self, memory_id: int) -> None:
        self._conn.execute("DELETE FROM memory WHERE id = ?", (memory_id,))
        self._conn.commit()

    def all_memories(self) -> list[dict]:
        """Every memory across all projects, with its project label (for the global assistant)."""
        rows = self._conn.execute(
            "SELECT m.id, m.vehicle_id, m.kind, m.content, m.embedding, m.created_at,"
            " v.label AS project, v.make, v.model, v.year"
            " FROM memory m JOIN vehicle v ON v.id = m.vehicle_id ORDER BY m.created_at DESC"
        ).fetchall()
        out = []
        for r in rows:
            d = self._memory_row(r)
            d["project"] = r["project"] or " ".join(
                filter(None, [r["year"], r["make"], r["model"]])
            ) or f"project {r['vehicle_id']}"
            out.append(d)
        return out

    # --- tags ------------------------------------------------------------------
    def add_tag(self, vehicle_id: int, tag: str) -> list[str]:
        tag = tag.strip()
        if tag and tag.lower() not in {t.lower() for t in self.list_tags(vehicle_id)}:
            self._conn.execute(
                "INSERT INTO tag (vehicle_id, tag, created_at) VALUES (?,?,?)",
                (vehicle_id, tag, _now()),
            )
            self._conn.commit()
        return self.list_tags(vehicle_id)

    def remove_tag(self, vehicle_id: int, tag: str) -> list[str]:
        self._conn.execute(
            "DELETE FROM tag WHERE vehicle_id = ? AND tag = ? COLLATE NOCASE", (vehicle_id, tag)
        )
        self._conn.commit()
        return self.list_tags(vehicle_id)

    def list_tags(self, vehicle_id: int) -> list[str]:
        rows = self._conn.execute(
            "SELECT tag FROM tag WHERE vehicle_id = ? ORDER BY tag COLLATE NOCASE", (vehicle_id,)
        ).fetchall()
        return [r["tag"] for r in rows]

    # --- chat ------------------------------------------------------------------
    def add_message(self, vehicle_id: int, role: str, content: str) -> dict:
        cur = self._conn.execute(
            "INSERT INTO message (vehicle_id, role, content, created_at) VALUES (?,?,?,?)",
            (vehicle_id, role, content, _now()),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM message WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_messages(self, vehicle_id: int, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM message WHERE vehicle_id = ? ORDER BY id ASC LIMIT ?",
            (vehicle_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
