"""Local SQLite store for vehicles, diagrams, pinouts, memories, and chat.

Deliberately simple (stdlib ``sqlite3``, no ORM) and local-only — a tech's diagrams and
VINs never leave the machine. Knowledge is keyed by vehicle so the AI can answer
per-vehicle questions and accumulate memories over time.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

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
    connector TEXT, pin TEXT, signal TEXT, wire_color TEXT, mating TEXT, notes TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    kind TEXT DEFAULT 'note', content TEXT NOT NULL,
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
        self._conn.commit()

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
        return [dict(r) for r in rows]

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
    def replace_pinouts(
        self, vehicle_id: int, diagram_id: int | None, rows: list[dict]
    ) -> list[dict]:
        """Replace this vehicle's pinouts with a freshly extracted set."""
        self._conn.execute("DELETE FROM pinout WHERE vehicle_id = ?", (vehicle_id,))
        for r in rows:
            self._conn.execute(
                "INSERT INTO pinout (vehicle_id, diagram_id, connector, pin, signal, wire_color,"
                " mating, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    vehicle_id, diagram_id,
                    str(r.get("connector", "")), str(r.get("pin", "")), str(r.get("signal", "")),
                    str(r.get("wire_color", "")), str(r.get("mating", "")), str(r.get("notes", "")),
                    _now(),
                ),
            )
        self._conn.commit()
        return self.list_pinouts(vehicle_id)

    def list_pinouts(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM pinout WHERE vehicle_id = ?"
            " ORDER BY connector, CAST(pin AS INTEGER), pin",
            (vehicle_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- memories --------------------------------------------------------------
    def add_memory(self, vehicle_id: int, content: str, *, kind: str = "note") -> dict:
        cur = self._conn.execute(
            "INSERT INTO memory (vehicle_id, kind, content, created_at) VALUES (?,?,?,?)",
            (vehicle_id, kind, content, _now()),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM memory WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_memories(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM memory WHERE vehicle_id = ? ORDER BY created_at DESC", (vehicle_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_memory(self, memory_id: int) -> None:
        self._conn.execute("DELETE FROM memory WHERE id = ?", (memory_id,))
        self._conn.commit()

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
