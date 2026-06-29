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


def make_store(config):
    """Return the store backend for `config`: Postgres+pgvector if CANOPY_DATABASE_URL is
    set, else the local SQLite Store."""
    if getattr(config, "database_url", ""):
        from canopy.vision.pgstore import PgStore

        return PgStore(config.database_url)
    return Store(config.db_path)


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
    role TEXT NOT NULL, content TEXT NOT NULL, channel TEXT DEFAULT 'chat',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attachment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    path TEXT NOT NULL, kind TEXT DEFAULT 'photo', note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pcb_component (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    attachment_id INTEGER, label TEXT, box TEXT, function TEXT, chk TEXT, part TEXT,
    confidence REAL, user_label TEXT, user_note TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profile (
    vehicle_id INTEGER PRIMARY KEY REFERENCES vehicle(id) ON DELETE CASCADE,
    yaml TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS measurement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    kind TEXT, label TEXT, mode TEXT, value REAL, unit TEXT, data TEXT,
    attachment_id INTEGER, note TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS project_access (
    user_id INTEGER NOT NULL, vehicle_id INTEGER NOT NULL, level TEXT NOT NULL DEFAULT 'read',
    PRIMARY KEY (user_id, vehicle_id)
);
CREATE TABLE IF NOT EXISTS org (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, color TEXT DEFAULT '#0f9d6b', x REAL, y REAL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS org_member (
    user_id INTEGER PRIMARY KEY, org_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS project_team (
    vehicle_id INTEGER PRIMARY KEY, org_id INTEGER NOT NULL, level TEXT NOT NULL DEFAULT 'read'
);
CREATE TABLE IF NOT EXISTS integration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, kind TEXT, base_url TEXT, auth_type TEXT, config TEXT, secret TEXT,
    enabled INTEGER DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE, part_number TEXT, make TEXT, model TEXT, year TEXT,
    module_class TEXT, label TEXT, profile_yaml TEXT, wiki TEXT, bom TEXT,
    symptoms TEXT, units INTEGER DEFAULT 1, source_vehicle_id INTEGER,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_diagram_vehicle ON diagram(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_pinout_vehicle ON pinout(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_memory_vehicle ON memory(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_tag_vehicle ON tag(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_message_vehicle ON message(vehicle_id, channel);
CREATE INDEX IF NOT EXISTS idx_attachment_vehicle ON attachment(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_pcb_vehicle ON pcb_component(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_pcb_attachment ON pcb_component(attachment_id);
CREATE INDEX IF NOT EXISTS idx_measurement_vehicle ON measurement(vehicle_id);
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
        msg = {r["name"] for r in self._conn.execute("PRAGMA table_info(message)")}
        if "channel" not in msg:
            self._conn.execute("ALTER TABLE message ADD COLUMN channel TEXT DEFAULT 'chat'")

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

    # --- chat / triage transcripts --------------------------------------------
    def add_message(
        self, vehicle_id: int, role: str, content: str, *, channel: str = "chat"
    ) -> dict:
        cur = self._conn.execute(
            "INSERT INTO message (vehicle_id, role, content, channel, created_at)"
            " VALUES (?,?,?,?,?)",
            (vehicle_id, role, content, channel, _now()),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM message WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_messages(
        self, vehicle_id: int, limit: int = 100, *, channel: str = "chat"
    ) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM message WHERE vehicle_id = ? AND channel = ? ORDER BY id ASC LIMIT ?",
            (vehicle_id, channel, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- attachments (triage photos: board, scope, meter) ----------------------
    def add_attachment(
        self, vehicle_id: int, path: str, *, kind: str = "photo", note: str = ""
    ) -> dict:
        cur = self._conn.execute(
            "INSERT INTO attachment (vehicle_id, path, kind, note, created_at) VALUES (?,?,?,?,?)",
            (vehicle_id, path, kind, note, _now()),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM attachment WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)

    def list_attachments(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM attachment WHERE vehicle_id = ? ORDER BY id DESC", (vehicle_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --- users & per-project access (Admin Console) ---
    def count_users(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM app_user").fetchone()[0]

    def create_user(self, username: str, password_hash: str, role: str = "user") -> dict:
        cur = self._conn.execute(
            "INSERT INTO app_user (username, password_hash, role, created_at) VALUES (?,?,?,?)",
            (username, password_hash, role, _now()))
        self._conn.commit()
        return self.get_user(cur.lastrowid)

    def get_user(self, uid: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM app_user WHERE id = ?", (uid,)).fetchone()
        return dict(row) if row else None

    def get_user_by_username(self, username: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM app_user WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

    def list_users(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, username, role, created_at FROM app_user ORDER BY id").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["projects"] = self._conn.execute(
                "SELECT COUNT(*) FROM project_access WHERE user_id = ?", (d["id"],)).fetchone()[0]
            out.append(d)
        return out

    def set_user_password(self, uid: int, password_hash: str) -> None:
        self._conn.execute(
            "UPDATE app_user SET password_hash = ? WHERE id = ?", (password_hash, uid))
        self._conn.commit()

    def delete_user(self, uid: int) -> None:
        self._conn.execute("DELETE FROM app_user WHERE id = ?", (uid,))
        self._conn.execute("DELETE FROM project_access WHERE user_id = ?", (uid,))
        self._conn.execute("DELETE FROM org_member WHERE user_id = ?", (uid,))
        self._conn.commit()

    # --- organizations / teams (bubble UI in the Admin Console) ---
    def list_orgs(self) -> list[dict]:
        orgs = [dict(r) for r in self._conn.execute("SELECT * FROM org ORDER BY id").fetchall()]
        by: dict[int, list[int]] = {}
        for r in self._conn.execute("SELECT org_id, user_id FROM org_member").fetchall():
            by.setdefault(r["org_id"], []).append(r["user_id"])
        for o in orgs:
            o["members"] = by.get(o["id"], [])
        return orgs

    def get_org(self, oid: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM org WHERE id = ?", (oid,)).fetchone()
        if not row:
            return None
        o = dict(row)
        o["members"] = [r["user_id"] for r in self._conn.execute(
            "SELECT user_id FROM org_member WHERE org_id = ?", (oid,)).fetchall()]
        return o

    def create_org(self, name: str, color: str = "#0f9d6b",
                   x: float | None = None, y: float | None = None) -> dict:
        cur = self._conn.execute(
            "INSERT INTO org (name, color, x, y, created_at) VALUES (?,?,?,?,?)",
            (name, color, x, y, _now()))
        self._conn.commit()
        return self.get_org(cur.lastrowid)

    def update_org(self, oid: int, **f) -> dict | None:
        cols, vals = [], []
        for k in ("name", "color", "x", "y"):
            if k in f and f[k] is not None:
                cols.append(f"{k} = ?")
                vals.append(f[k])
        if cols:
            self._conn.execute(f"UPDATE org SET {', '.join(cols)} WHERE id = ?", (*vals, oid))
            self._conn.commit()
        return self.get_org(oid)

    def delete_org(self, oid: int) -> None:
        self._conn.execute("DELETE FROM org WHERE id = ?", (oid,))
        self._conn.execute("DELETE FROM org_member WHERE org_id = ?", (oid,))
        self._conn.execute("DELETE FROM project_team WHERE org_id = ?", (oid,))
        self._conn.commit()

    def team_of_user(self, uid: int) -> dict | None:
        row = self._conn.execute(
            "SELECT o.* FROM org o JOIN org_member m ON m.org_id = o.id WHERE m.user_id = ?",
            (uid,)).fetchone()
        return dict(row) if row else None

    def set_project_team(self, vehicle_id: int, org_id: int | None, level: str = "read") -> None:
        if org_id is None:
            self._conn.execute("DELETE FROM project_team WHERE vehicle_id = ?", (vehicle_id,))
        else:
            self._conn.execute(
                "INSERT INTO project_team (vehicle_id, org_id, level) VALUES (?,?,?) "
                "ON CONFLICT(vehicle_id) DO UPDATE SET org_id = excluded.org_id, "
                "level = excluded.level",
                (vehicle_id, org_id, level))
        self._conn.commit()

    def project_team_map(self) -> dict[int, dict]:
        return {r["vehicle_id"]: {"org_id": r["org_id"], "level": r["level"]}
                for r in self._conn.execute("SELECT * FROM project_team").fetchall()}

    def org_access_map(self, org_id: int) -> dict[int, str]:
        return {r["vehicle_id"]: r["level"] for r in self._conn.execute(
            "SELECT vehicle_id, level FROM project_team WHERE org_id = ?", (org_id,)).fetchall()}

    def assign_org(self, user_id: int, org_id: int | None) -> None:
        if org_id is None:
            self._conn.execute("DELETE FROM org_member WHERE user_id = ?", (user_id,))
        else:
            self._conn.execute(
                "INSERT INTO org_member (user_id, org_id) VALUES (?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET org_id = excluded.org_id", (user_id, org_id))
        self._conn.commit()

    def set_access(self, uid: int, vehicle_id: int, level: str | None) -> None:
        if level in (None, "", "none"):
            self._conn.execute(
                "DELETE FROM project_access WHERE user_id = ? AND vehicle_id = ?",
                (uid, vehicle_id))
        else:
            self._conn.execute(
                "INSERT INTO project_access (user_id, vehicle_id, level) VALUES (?,?,?) "
                "ON CONFLICT(user_id, vehicle_id) DO UPDATE SET level = excluded.level",
                (uid, vehicle_id, level))
        self._conn.commit()

    def access_map(self, uid: int) -> dict[int, str]:
        rows = self._conn.execute(
            "SELECT vehicle_id, level FROM project_access WHERE user_id = ?", (uid,)).fetchall()
        return {r["vehicle_id"]: r["level"] for r in rows}

    def access_level(self, uid: int, vehicle_id: int) -> str | None:
        row = self._conn.execute(
            "SELECT level FROM project_access WHERE user_id = ? AND vehicle_id = ?",
            (uid, vehicle_id)).fetchone()
        return row["level"] if row else None

    # --- third-party integrations (Admin Console) ---
    @staticmethod
    def _integration_public(row: dict) -> dict:
        d = dict(row)
        sec = d.pop("secret", None)
        d["has_secret"] = bool(sec)
        d["secret_hint"] = ("••••" + sec[-4:]) if sec and len(sec) >= 4 else ("••••" if sec else "")
        d["config"] = json.loads(d["config"]) if d.get("config") else {}
        d["enabled"] = bool(d.get("enabled"))
        return d

    def list_integrations(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM integration ORDER BY id").fetchall()
        return [self._integration_public(dict(r)) for r in rows]

    def get_integration(self, integ_id: int, *, with_secret: bool = False) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM integration WHERE id = ?", (integ_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if with_secret:
            d["config"] = json.loads(d["config"]) if d.get("config") else {}
            return d
        return self._integration_public(d)

    def add_integration(self, **f) -> dict:
        cur = self._conn.execute(
            "INSERT INTO integration (name, kind, base_url, auth_type, config, secret, enabled,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (f.get("name", ""), f.get("kind", "rest"), f.get("base_url", ""),
             f.get("auth_type", "none"), json.dumps(f.get("config") or {}),
             f.get("secret") or None, 1 if f.get("enabled", True) else 0, _now(), _now()))
        self._conn.commit()
        return self.get_integration(cur.lastrowid)

    def update_integration(self, integ_id: int, **f) -> dict | None:
        cols, vals = [], []
        for k in ("name", "kind", "base_url", "auth_type", "enabled"):
            if k in f and f[k] is not None:
                cols.append(f"{k} = ?")
                vals.append(1 if (k == "enabled" and f[k]) else (0 if k == "enabled" else f[k]))
        if f.get("config") is not None:
            cols.append("config = ?")
            vals.append(json.dumps(f["config"]))
        if f.get("secret"):  # only overwrite the secret when a new one is provided
            cols.append("secret = ?")
            vals.append(f["secret"])
        if cols:
            cols.append("updated_at = ?")
            vals.append(_now())
            self._conn.execute(
                f"UPDATE integration SET {', '.join(cols)} WHERE id = ?", (*vals, integ_id))
            self._conn.commit()
        return self.get_integration(integ_id)

    def delete_integration(self, integ_id: int) -> None:
        self._conn.execute("DELETE FROM integration WHERE id = ?", (integ_id,))
        self._conn.commit()

    def project_stats(self, vehicle_id: int) -> dict:
        """Cheap existence counts for the Cockpit readiness view."""
        def cnt(table: str) -> int:
            return self._conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE vehicle_id = ?", (vehicle_id,)).fetchone()[0]
        return {
            "diagrams": cnt("diagram"), "pinouts": cnt("pinout"),
            "components": cnt("pcb_component"), "memories": cnt("memory"),
            "measurements": cnt("measurement"), "has_profile": cnt("profile") > 0,
        }

    # --- product library (reusable SKU: profile + wiki + BOM + cases) ---
    _PRODUCT_COLS = ("sku", "part_number", "make", "model", "year", "module_class", "label",
                     "profile_yaml", "wiki", "bom", "symptoms", "source_vehicle_id")

    def get_product_by_sku(self, sku: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM product WHERE sku = ?", (sku,)).fetchone()
        return dict(row) if row else None

    def upsert_product(self, **f) -> dict:
        """Create or update a product keyed by sku; bumps units on each (re)promote."""
        existing = self.get_product_by_sku(f.get("sku", ""))
        if existing:
            cols = [c for c in self._PRODUCT_COLS if c in f]
            sets = ", ".join(f"{c} = ?" for c in cols)
            self._conn.execute(
                f"UPDATE product SET {sets}, units = units + 1, updated_at = ? WHERE id = ?",
                (*[f[c] for c in cols], _now(), existing["id"]))
            self._conn.commit()
            return self.get_product(existing["id"])
        cols = list(self._PRODUCT_COLS)
        self._conn.execute(
            f"INSERT INTO product ({', '.join(cols)}, units, created_at, updated_at)"
            f" VALUES ({', '.join('?' for _ in cols)}, 1, ?, ?)",
            (*[f.get(c) for c in cols], _now(), _now()))
        self._conn.commit()
        return self.get_product_by_sku(f.get("sku", ""))

    def get_product(self, product_id: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM product WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None

    def list_products(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, sku, part_number, make, model, year, module_class, label, units,"
            " updated_at FROM product ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    def match_product(self, *, sku: str = "", make: str = "", model: str = "",
                      year: str = "") -> dict | None:
        if sku:
            m = self.get_product_by_sku(sku)
            if m:
                return m
        if make and model:
            row = self._conn.execute(
                "SELECT * FROM product WHERE lower(make)=lower(?) AND lower(model)=lower(?)"
                " AND (year=? OR ?='') ORDER BY units DESC LIMIT 1",
                (make, model, year, year)).fetchone()
            return dict(row) if row else None
        return None

    def delete_product(self, product_id: int) -> None:
        self._conn.execute("DELETE FROM product WHERE id = ?", (product_id,))
        self._conn.commit()

    # --- recorded measurements (DMM readings / scope captures for the wiki) ---
    def add_measurement(self, vehicle_id: int, **f) -> dict:
        cur = self._conn.execute(
            "INSERT INTO measurement (vehicle_id, kind, label, mode, value, unit, data,"
            " attachment_id, note, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (vehicle_id, f.get("kind", ""), f.get("label", ""), f.get("mode", ""),
             f.get("value"), f.get("unit", ""), f.get("data"), f.get("attachment_id"),
             f.get("note", ""), _now()))
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM measurement WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    def list_measurements(self, vehicle_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM measurement WHERE vehicle_id = ? ORDER BY id DESC", (vehicle_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_measurement(self, measurement_id: int) -> None:
        self._conn.execute("DELETE FROM measurement WHERE id = ?", (measurement_id,))
        self._conn.commit()

    # --- module profile (the CAB contract) ---
    def get_profile(self, vehicle_id: int) -> str | None:
        row = self._conn.execute(
            "SELECT yaml FROM profile WHERE vehicle_id = ?", (vehicle_id,)).fetchone()
        return row["yaml"] if row else None

    def save_profile(self, vehicle_id: int, yaml_text: str) -> None:
        self._conn.execute(
            "INSERT INTO profile (vehicle_id, yaml, updated_at) VALUES (?,?,?)"
            " ON CONFLICT(vehicle_id) DO UPDATE SET yaml = excluded.yaml,"
            " updated_at = excluded.updated_at", (vehicle_id, yaml_text, _now()))
        self._conn.commit()

    def get_attachment(self, attachment_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM attachment WHERE id = ?", (attachment_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_attachment(self, attachment_id: int, *, note: str) -> dict | None:
        self._conn.execute(
            "UPDATE attachment SET note = ? WHERE id = ?", (note, attachment_id))
        self._conn.commit()
        return self.get_attachment(attachment_id)

    # --- PCB components (boxed parts + user corrections) ---
    @staticmethod
    def _pcb_row(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["box"] = json.loads(d["box"]) if d.get("box") else []
        d["check"] = d.pop("chk", "") or ""
        return d

    def _insert_pcb(self, vehicle_id: int, attachment_id: int | None, c: dict) -> int:
        cur = self._conn.execute(
            "INSERT INTO pcb_component (vehicle_id, attachment_id, label, box, function,"
            " chk, part, confidence, user_label, user_note, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (vehicle_id, attachment_id, c.get("label", ""), json.dumps(c.get("box", [])),
             c.get("function", ""), c.get("check", ""), c.get("part", ""),
             float(c.get("confidence", 0) or 0), c.get("user_label"), c.get("user_note"), _now()),
        )
        return cur.lastrowid

    def replace_pcb_components(
        self, vehicle_id: int, attachment_id: int | None, comps: list[dict]
    ) -> list[dict]:
        """Store an analysis for ONE board photo, replacing only that photo's components
        (other photos in the project are kept, so a project can hold many boards)."""
        if attachment_id is not None:
            self._conn.execute(
                "DELETE FROM pcb_component WHERE attachment_id = ?", (attachment_id,))
        for c in comps:
            self._insert_pcb(vehicle_id, attachment_id, c)
        self._conn.commit()
        return self.list_pcb_components(vehicle_id, attachment_id)

    def add_pcb_component(self, vehicle_id: int, attachment_id: int | None, comp: dict) -> dict:
        cid = self._insert_pcb(vehicle_id, attachment_id, comp)
        self._conn.commit()
        return self._pcb_row(self._conn.execute(
            "SELECT * FROM pcb_component WHERE id = ?", (cid,)).fetchone())

    def delete_pcb_component(self, comp_id: int) -> None:
        self._conn.execute("DELETE FROM pcb_component WHERE id = ?", (comp_id,))
        self._conn.commit()

    def list_pcb_components(
        self, vehicle_id: int, attachment_id: int | None = None
    ) -> list[dict]:
        if attachment_id is not None:
            rows = self._conn.execute(
                "SELECT * FROM pcb_component WHERE vehicle_id = ? AND attachment_id = ?"
                " ORDER BY id", (vehicle_id, attachment_id)).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM pcb_component WHERE vehicle_id = ? ORDER BY id",
                (vehicle_id,)).fetchall()
        return [self._pcb_row(r) for r in rows]

    def list_pcb_photos(self, vehicle_id: int) -> list[dict]:
        """PCB board photos in this project (newest first), with a component count."""
        rows = self._conn.execute(
            "SELECT a.id, a.note, a.created_at, COUNT(c.id) AS count FROM attachment a"
            " LEFT JOIN pcb_component c ON c.attachment_id = a.id"
            " WHERE a.vehicle_id = ? AND a.kind = 'pcb' GROUP BY a.id ORDER BY a.id DESC",
            (vehicle_id,)).fetchall()
        return [dict(r) for r in rows]

    def latest_pcb_attachment(self, vehicle_id: int) -> int | None:
        row = self._conn.execute(
            "SELECT attachment_id FROM pcb_component WHERE vehicle_id = ?"
            " ORDER BY id DESC LIMIT 1", (vehicle_id,)
        ).fetchone()
        return row["attachment_id"] if row else None

    def update_pcb_component(self, comp_id: int, **fields) -> dict | None:
        allowed = {"user_label", "user_note", "label", "part", "function", "confidence"}
        sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "check" in fields and fields["check"] is not None:
            sets["chk"] = fields["check"]
        if "box" in fields and fields["box"] is not None:
            sets["box"] = json.dumps(fields["box"])
        if sets:
            cols = ", ".join(f"{k} = ?" for k in sets)
            self._conn.execute(
                f"UPDATE pcb_component SET {cols} WHERE id = ?", (*sets.values(), comp_id)
            )
            self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM pcb_component WHERE id = ?", (comp_id,)
        ).fetchone()
        return self._pcb_row(row) if row else None
