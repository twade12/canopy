"""Postgres + pgvector backend for the vision store (GAMEPLAN §Phase 1).

Same method surface as the SQLite :class:`~canopy.vision.store.Store`, so it is a drop-in
when ``CANOPY_DATABASE_URL`` points at a Postgres with the ``vector`` extension (e.g. the
``timescale/timescaledb-ha`` image in docker-compose). This moves the knowledge base off a
single-process SQLite file to a shared database — the prerequisite for org-wide semantic
search and many technicians working at once.

Embeddings are stored in a real ``vector`` column; today retrieval still happens in Python
(the app ranks candidates), but the column is in place for server-side ANN search later.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import psycopg
from pgvector import Vector
from psycopg.rows import dict_row

from canopy.vision.store import normalize_connector

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS vehicle (
    id SERIAL PRIMARY KEY,
    vin TEXT, year TEXT, make TEXT, model TEXT, label TEXT, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS diagram (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    filename TEXT, path TEXT NOT NULL, mime TEXT, pages INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS pinout (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    diagram_id INTEGER REFERENCES diagram(id) ON DELETE SET NULL,
    connector TEXT, pin TEXT, signal TEXT, function TEXT, wire_color TEXT,
    circuit TEXT, connects_to TEXT, mating TEXT, notes TEXT, page INTEGER,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS memory (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    kind TEXT DEFAULT 'note', content TEXT NOT NULL, embedding vector,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS tag (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    tag TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS message (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    role TEXT NOT NULL, content TEXT NOT NULL, channel TEXT DEFAULT 'chat',
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS attachment (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    path TEXT NOT NULL, kind TEXT DEFAULT 'photo', note TEXT, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS pcb_component (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    attachment_id INTEGER, label TEXT, box TEXT, function TEXT, chk TEXT, part TEXT,
    confidence REAL, user_label TEXT, user_note TEXT, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS profile (
    vehicle_id INTEGER PRIMARY KEY REFERENCES vehicle(id) ON DELETE CASCADE,
    yaml TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS measurement (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicle(id) ON DELETE CASCADE,
    kind TEXT, label TEXT, mode TEXT, value REAL, unit TEXT, data TEXT,
    attachment_id INTEGER, note TEXT, created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS app_user (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS project_access (
    user_id INTEGER NOT NULL, vehicle_id INTEGER NOT NULL, level TEXT NOT NULL DEFAULT 'read',
    PRIMARY KEY (user_id, vehicle_id)
);
CREATE TABLE IF NOT EXISTS integration (
    id SERIAL PRIMARY KEY,
    name TEXT, kind TEXT, base_url TEXT, auth_type TEXT, config TEXT, secret TEXT,
    enabled INTEGER DEFAULT 1, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS product (
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE, part_number TEXT, make TEXT, model TEXT, year TEXT,
    module_class TEXT, label TEXT, profile_yaml TEXT, wiki TEXT, bom TEXT,
    symptoms TEXT, units INTEGER DEFAULT 1, source_vehicle_id INTEGER,
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PgStore:
    """Postgres-backed store; mirrors :class:`canopy.vision.store.Store`."""

    def __init__(self, dsn: str):
        self._conn = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        with self._conn.cursor() as cur:
            cur.execute(SCHEMA)
        from pgvector.psycopg import register_vector

        register_vector(self._conn)

    def close(self) -> None:
        self._conn.close()

    def _one(self, sql: str, params: tuple = ()) -> dict | None:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def _all(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())

    @staticmethod
    def _emb(row: dict) -> dict:
        if "embedding" in row and row["embedding"] is not None:
            row["embedding"] = [float(x) for x in row["embedding"]]
        return row

    # --- vehicles --------------------------------------------------------------
    def create_vehicle(self, *, vin="", year="", make="", model="", label="") -> dict:
        return self._one(
            "INSERT INTO vehicle (vin,year,make,model,label,created_at)"
            " VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
            (vin, year, make, model, label, _now()),
        )

    def update_vehicle(self, vehicle_id: int, **fields) -> dict:
        allowed = {"vin", "year", "make", "model", "label"}
        sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if sets:
            cols = ", ".join(f"{k} = %s" for k in sets)
            self._one(f"UPDATE vehicle SET {cols} WHERE id = %s RETURNING id",
                      (*sets.values(), vehicle_id))
        return self.get_vehicle(vehicle_id)

    def get_vehicle(self, vehicle_id: int) -> dict:
        row = self._one("SELECT * FROM vehicle WHERE id = %s", (vehicle_id,))
        if row is None:
            raise KeyError(f"no vehicle {vehicle_id}")
        return row

    def list_vehicles(self) -> list[dict]:
        rows = self._all("SELECT * FROM vehicle ORDER BY created_at DESC")
        for r in rows:
            r["tags"] = self.list_tags(r["id"])
        return rows

    def delete_vehicle(self, vehicle_id: int) -> None:
        self._one("DELETE FROM vehicle WHERE id = %s RETURNING id", (vehicle_id,))

    # --- diagrams --------------------------------------------------------------
    def add_diagram(self, vehicle_id, *, filename, path, mime, pages=1) -> dict:
        return self._one(
            "INSERT INTO diagram (vehicle_id,filename,path,mime,pages,created_at)"
            " VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
            (vehicle_id, filename, path, mime, pages, _now()),
        )

    def get_diagram(self, diagram_id: int) -> dict:
        row = self._one("SELECT * FROM diagram WHERE id = %s", (diagram_id,))
        if row is None:
            raise KeyError(f"no diagram {diagram_id}")
        return row

    def list_diagrams(self, vehicle_id: int) -> list[dict]:
        return self._all(
            "SELECT * FROM diagram WHERE vehicle_id = %s ORDER BY created_at DESC", (vehicle_id,)
        )

    def latest_diagram(self, vehicle_id: int) -> dict | None:
        rows = self.list_diagrams(vehicle_id)
        return rows[0] if rows else None

    # --- pinouts ---------------------------------------------------------------
    def _insert_pinout(self, vehicle_id, diagram_id, page, r: dict) -> None:
        self._one(
            "INSERT INTO pinout (vehicle_id,diagram_id,connector,pin,signal,function,wire_color,"
            "circuit,connects_to,mating,notes,page,created_at)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (vehicle_id, diagram_id, str(r.get("connector", "")), str(r.get("pin", "")),
             str(r.get("signal", "")), str(r.get("function", "")), str(r.get("wire_color", "")),
             str(r.get("circuit", "")), str(r.get("connects_to", "")), str(r.get("mating", "")),
             str(r.get("notes", "")), page, _now()),
        )

    def merge_pinouts(self, vehicle_id, diagram_id, page, rows: list[dict]) -> list[dict]:
        for r in rows:
            pin = str(r.get("pin", ""))
            if not pin:
                continue
            r = {**r, "connector": normalize_connector(r.get("connector", ""))}
            self._one(
                "DELETE FROM pinout WHERE vehicle_id=%s AND connector=%s AND pin=%s RETURNING id",
                (vehicle_id, r["connector"], pin))
            self._insert_pinout(vehicle_id, diagram_id, page, r)
        return self.list_pinouts(vehicle_id)

    def replace_pinouts(self, vehicle_id, diagram_id, rows, page=None) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM pinout WHERE vehicle_id = %s", (vehicle_id,))
        for r in rows:
            self._insert_pinout(vehicle_id, diagram_id, page, r)
        return self.list_pinouts(vehicle_id)

    def clear_pinouts(self, vehicle_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM pinout WHERE vehicle_id = %s", (vehicle_id,))

    def list_pinouts(self, vehicle_id: int) -> list[dict]:
        return self._all(
            "SELECT * FROM pinout WHERE vehicle_id = %s"
            " ORDER BY connector, NULLIF(regexp_replace(pin,'\\D','','g'),'')::int NULLS LAST, pin",
            (vehicle_id,),
        )

    # --- memories --------------------------------------------------------------
    def add_memory(self, vehicle_id, content, *, kind="note", embedding=None) -> dict:
        emb = Vector([float(x) for x in embedding]) if embedding else None
        row = self._one(
            "INSERT INTO memory (vehicle_id,kind,content,embedding,created_at)"
            " VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (vehicle_id, kind, content, emb, _now()),
        )
        return self._emb(row)

    def list_memories(self, vehicle_id: int) -> list[dict]:
        return [self._emb(r) for r in self._all(
            "SELECT * FROM memory WHERE vehicle_id = %s ORDER BY created_at DESC", (vehicle_id,))]

    def delete_memory(self, memory_id: int) -> None:
        self._one("DELETE FROM memory WHERE id = %s RETURNING id", (memory_id,))

    def search_memories(
        self, query: list[float], k: int = 10, vehicle_id: int | None = None
    ) -> list[dict]:
        """Top-k memories by cosine similarity (server-side pgvector `<=>`)."""
        if not query:
            return []
        query = Vector([float(x) for x in query])
        sql = ("SELECT m.id, m.vehicle_id, m.kind, m.content, m.created_at, v.label,"
               " 1 - (m.embedding <=> %s) AS score"
               " FROM memory m JOIN vehicle v ON v.id = m.vehicle_id"
               " WHERE m.embedding IS NOT NULL")
        params: list = [query]
        if vehicle_id is not None:
            sql += " AND m.vehicle_id = %s"
            params.append(vehicle_id)
        sql += " ORDER BY m.embedding <=> %s LIMIT %s"
        params += [query, k]
        rows = self._all(sql, tuple(params))
        for r in rows:
            r["project"] = r.get("label") or f"project {r['vehicle_id']}"
        return rows

    def all_memories(self) -> list[dict]:
        rows = self._all(
            "SELECT m.id,m.vehicle_id,m.kind,m.content,m.embedding,m.created_at,"
            " v.label,v.make,v.model,v.year FROM memory m JOIN vehicle v ON v.id=m.vehicle_id"
            " ORDER BY m.created_at DESC"
        )
        out = []
        for r in rows:
            self._emb(r)
            r["project"] = r.get("label") or " ".join(
                filter(None, [r.get("year"), r.get("make"), r.get("model")])
            ) or f"project {r['vehicle_id']}"
            out.append(r)
        return out

    # --- tags ------------------------------------------------------------------
    def add_tag(self, vehicle_id: int, tag: str) -> list[str]:
        tag = tag.strip()
        if tag and tag.lower() not in {t.lower() for t in self.list_tags(vehicle_id)}:
            self._one("INSERT INTO tag (vehicle_id,tag,created_at) VALUES (%s,%s,%s) RETURNING id",
                      (vehicle_id, tag, _now()))
        return self.list_tags(vehicle_id)

    def remove_tag(self, vehicle_id: int, tag: str) -> list[str]:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM tag WHERE vehicle_id=%s AND lower(tag)=lower(%s)",
                        (vehicle_id, tag))
        return self.list_tags(vehicle_id)

    def list_tags(self, vehicle_id: int) -> list[str]:
        return [r["tag"] for r in self._all(
            "SELECT tag FROM tag WHERE vehicle_id = %s ORDER BY lower(tag)", (vehicle_id,))]

    # --- messages / attachments ------------------------------------------------
    def add_message(self, vehicle_id, role, content, *, channel="chat") -> dict:
        return self._one(
            "INSERT INTO message (vehicle_id,role,content,channel,created_at)"
            " VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (vehicle_id, role, content, channel, _now()),
        )

    def list_messages(self, vehicle_id, limit=100, *, channel="chat") -> list[dict]:
        return self._all(
            "SELECT * FROM message WHERE vehicle_id=%s AND channel=%s ORDER BY id ASC LIMIT %s",
            (vehicle_id, channel, limit),
        )

    def add_attachment(self, vehicle_id, path, *, kind="photo", note="") -> dict:
        return self._one(
            "INSERT INTO attachment (vehicle_id,path,kind,note,created_at)"
            " VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (vehicle_id, path, kind, note, _now()),
        )

    def list_attachments(self, vehicle_id: int) -> list[dict]:
        return self._all(
            "SELECT * FROM attachment WHERE vehicle_id = %s ORDER BY id DESC", (vehicle_id,))

    def get_attachment(self, attachment_id: int) -> dict | None:
        return self._one("SELECT * FROM attachment WHERE id = %s", (attachment_id,))

    # --- users & per-project access (Admin Console) ---
    def count_users(self) -> int:
        return self._one("SELECT COUNT(*) AS n FROM app_user")["n"]

    def create_user(self, username: str, password_hash: str, role: str = "user") -> dict:
        r = self._one(
            "INSERT INTO app_user (username, password_hash, role, created_at) "
            "VALUES (%s,%s,%s,%s) RETURNING id", (username, password_hash, role, _now()))
        return self.get_user(r["id"])

    def get_user(self, uid: int) -> dict | None:
        return self._one("SELECT * FROM app_user WHERE id = %s", (uid,))

    def get_user_by_username(self, username: str) -> dict | None:
        return self._one("SELECT * FROM app_user WHERE username = %s", (username,))

    def list_users(self) -> list[dict]:
        return self._all(
            "SELECT u.id, u.username, u.role, u.created_at, "
            "(SELECT COUNT(*) FROM project_access p WHERE p.user_id = u.id) AS projects "
            "FROM app_user u ORDER BY u.id")

    def set_user_password(self, uid: int, password_hash: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE app_user SET password_hash = %s WHERE id = %s", (password_hash, uid))

    def delete_user(self, uid: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM app_user WHERE id = %s", (uid,))
            cur.execute("DELETE FROM project_access WHERE user_id = %s", (uid,))

    def set_access(self, uid: int, vehicle_id: int, level: str | None) -> None:
        with self._conn.cursor() as cur:
            if level in (None, "", "none"):
                cur.execute(
                    "DELETE FROM project_access WHERE user_id = %s AND vehicle_id = %s",
                    (uid, vehicle_id))
            else:
                cur.execute(
                    "INSERT INTO project_access (user_id, vehicle_id, level) VALUES (%s,%s,%s) "
                    "ON CONFLICT(user_id, vehicle_id) DO UPDATE SET level = excluded.level",
                    (uid, vehicle_id, level))

    def access_map(self, uid: int) -> dict[int, str]:
        rows = self._all(
            "SELECT vehicle_id, level FROM project_access WHERE user_id = %s", (uid,))
        return {r["vehicle_id"]: r["level"] for r in rows}

    def access_level(self, uid: int, vehicle_id: int) -> str | None:
        row = self._one(
            "SELECT level FROM project_access WHERE user_id = %s AND vehicle_id = %s",
            (uid, vehicle_id))
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
        return [self._integration_public(r) for r in
                self._all("SELECT * FROM integration ORDER BY id")]

    def get_integration(self, integ_id: int, *, with_secret: bool = False) -> dict | None:
        row = self._one("SELECT * FROM integration WHERE id = %s", (integ_id,))
        if not row:
            return None
        if with_secret:
            row = dict(row)
            row["config"] = json.loads(row["config"]) if row.get("config") else {}
            return row
        return self._integration_public(row)

    def add_integration(self, **f) -> dict:
        r = self._one(
            "INSERT INTO integration (name, kind, base_url, auth_type, config, secret, enabled,"
            " created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (f.get("name", ""), f.get("kind", "rest"), f.get("base_url", ""),
             f.get("auth_type", "none"), json.dumps(f.get("config") or {}),
             f.get("secret") or None, 1 if f.get("enabled", True) else 0, _now(), _now()))
        return self.get_integration(r["id"])

    def update_integration(self, integ_id: int, **f) -> dict | None:
        cols, vals = [], []
        for k in ("name", "kind", "base_url", "auth_type", "enabled"):
            if k in f and f[k] is not None:
                cols.append(f"{k} = %s")
                vals.append(1 if (k == "enabled" and f[k]) else (0 if k == "enabled" else f[k]))
        if f.get("config") is not None:
            cols.append("config = %s")
            vals.append(json.dumps(f["config"]))
        if f.get("secret"):
            cols.append("secret = %s")
            vals.append(f["secret"])
        if cols:
            cols.append("updated_at = %s")
            vals.append(_now())
            with self._conn.cursor() as cur:
                cur.execute(
                    f"UPDATE integration SET {', '.join(cols)} WHERE id = %s", (*vals, integ_id))
        return self.get_integration(integ_id)

    def delete_integration(self, integ_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM integration WHERE id = %s", (integ_id,))

    def project_stats(self, vehicle_id: int) -> dict:
        def cnt(table: str) -> int:
            return self._one(
                f"SELECT COUNT(*) AS n FROM {table} WHERE vehicle_id = %s", (vehicle_id,))["n"]
        return {
            "diagrams": cnt("diagram"), "pinouts": cnt("pinout"),
            "components": cnt("pcb_component"), "memories": cnt("memory"),
            "measurements": cnt("measurement"), "has_profile": cnt("profile") > 0,
        }

    # --- product library ---
    _PRODUCT_COLS = ("sku", "part_number", "make", "model", "year", "module_class", "label",
                     "profile_yaml", "wiki", "bom", "symptoms", "source_vehicle_id")

    def get_product_by_sku(self, sku: str) -> dict | None:
        return self._one("SELECT * FROM product WHERE sku = %s", (sku,))

    def upsert_product(self, **f) -> dict:
        existing = self.get_product_by_sku(f.get("sku", ""))
        if existing:
            cols = [c for c in self._PRODUCT_COLS if c in f]
            sets = ", ".join(f"{c} = %s" for c in cols)
            return self._one(
                f"UPDATE product SET {sets}, units = units + 1, updated_at = %s"
                " WHERE id = %s RETURNING *",
                (*[f[c] for c in cols], _now(), existing["id"]))
        cols = list(self._PRODUCT_COLS)
        ph = ", ".join(["%s"] * len(cols))
        return self._one(
            f"INSERT INTO product ({', '.join(cols)}, units, created_at, updated_at)"
            f" VALUES ({ph}, 1, %s, %s) RETURNING *",
            (*[f.get(c) for c in cols], _now(), _now()))

    def get_product(self, product_id: int) -> dict | None:
        return self._one("SELECT * FROM product WHERE id = %s", (product_id,))

    def list_products(self) -> list[dict]:
        return self._all(
            "SELECT id, sku, part_number, make, model, year, module_class, label, units,"
            " updated_at FROM product ORDER BY updated_at DESC")

    def match_product(self, *, sku: str = "", make: str = "", model: str = "",
                      year: str = "") -> dict | None:
        if sku:
            m = self.get_product_by_sku(sku)
            if m:
                return m
        if make and model:
            return self._one(
                "SELECT * FROM product WHERE lower(make)=lower(%s) AND lower(model)=lower(%s)"
                " AND (year=%s OR %s='') ORDER BY units DESC LIMIT 1",
                (make, model, year, year))
        return None

    def delete_product(self, product_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM product WHERE id = %s", (product_id,))

    # --- recorded measurements ---
    def add_measurement(self, vehicle_id: int, **f) -> dict:
        return self._one(
            "INSERT INTO measurement (vehicle_id, kind, label, mode, value, unit, data,"
            " attachment_id, note, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (vehicle_id, f.get("kind", ""), f.get("label", ""), f.get("mode", ""),
             f.get("value"), f.get("unit", ""), f.get("data"), f.get("attachment_id"),
             f.get("note", ""), _now()))

    def list_measurements(self, vehicle_id: int) -> list[dict]:
        return self._all(
            "SELECT * FROM measurement WHERE vehicle_id = %s ORDER BY id DESC", (vehicle_id,))

    def delete_measurement(self, measurement_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM measurement WHERE id = %s", (measurement_id,))

    # --- module profile (the CAB contract) ---
    def get_profile(self, vehicle_id: int) -> str | None:
        row = self._one("SELECT yaml FROM profile WHERE vehicle_id = %s", (vehicle_id,))
        return row["yaml"] if row else None

    def save_profile(self, vehicle_id: int, yaml_text: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO profile (vehicle_id, yaml, updated_at) VALUES (%s,%s,%s)"
                " ON CONFLICT (vehicle_id) DO UPDATE SET yaml = EXCLUDED.yaml,"
                " updated_at = EXCLUDED.updated_at", (vehicle_id, yaml_text, _now()))

    def update_attachment(self, attachment_id: int, *, note: str) -> dict | None:
        return self._one(
            "UPDATE attachment SET note = %s WHERE id = %s RETURNING *", (note, attachment_id))

    # --- PCB components (boxed parts + user corrections) ---
    @staticmethod
    def _pcb_row(row: dict) -> dict:
        d = dict(row)
        d["box"] = json.loads(d["box"]) if d.get("box") else []
        d["check"] = d.pop("chk", "") or ""
        return d

    def _insert_pcb(self, cur, vehicle_id: int, attachment_id: int | None, c: dict) -> int:
        cur.execute(
            "INSERT INTO pcb_component (vehicle_id, attachment_id, label, box, function,"
            " chk, part, confidence, user_label, user_note, created_at)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (vehicle_id, attachment_id, c.get("label", ""), json.dumps(c.get("box", [])),
             c.get("function", ""), c.get("check", ""), c.get("part", ""),
             float(c.get("confidence", 0) or 0), c.get("user_label"), c.get("user_note"), _now()),
        )
        return cur.fetchone()["id"]

    def replace_pcb_components(
        self, vehicle_id: int, attachment_id: int | None, comps: list[dict]
    ) -> list[dict]:
        with self._conn.cursor() as cur:
            if attachment_id is not None:
                cur.execute(
                    "DELETE FROM pcb_component WHERE attachment_id = %s", (attachment_id,))
            for c in comps:
                self._insert_pcb(cur, vehicle_id, attachment_id, c)
        return self.list_pcb_components(vehicle_id, attachment_id)

    def add_pcb_component(self, vehicle_id: int, attachment_id: int | None, comp: dict) -> dict:
        with self._conn.cursor() as cur:
            cid = self._insert_pcb(cur, vehicle_id, attachment_id, comp)
        return self._pcb_row(self._one("SELECT * FROM pcb_component WHERE id = %s", (cid,)))

    def delete_pcb_component(self, comp_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM pcb_component WHERE id = %s", (comp_id,))

    def list_pcb_components(
        self, vehicle_id: int, attachment_id: int | None = None
    ) -> list[dict]:
        if attachment_id is not None:
            rows = self._all(
                "SELECT * FROM pcb_component WHERE vehicle_id = %s AND attachment_id = %s"
                " ORDER BY id", (vehicle_id, attachment_id))
        else:
            rows = self._all(
                "SELECT * FROM pcb_component WHERE vehicle_id = %s ORDER BY id", (vehicle_id,))
        return [self._pcb_row(r) for r in rows]

    def list_pcb_photos(self, vehicle_id: int) -> list[dict]:
        return self._all(
            "SELECT a.id, a.note, a.created_at, COUNT(c.id) AS count FROM attachment a"
            " LEFT JOIN pcb_component c ON c.attachment_id = a.id"
            " WHERE a.vehicle_id = %s AND a.kind = 'pcb' GROUP BY a.id ORDER BY a.id DESC",
            (vehicle_id,))

    def latest_pcb_attachment(self, vehicle_id: int) -> int | None:
        row = self._one(
            "SELECT attachment_id FROM pcb_component WHERE vehicle_id = %s"
            " ORDER BY id DESC LIMIT 1", (vehicle_id,))
        return row["attachment_id"] if row else None

    def update_pcb_component(self, comp_id: int, **fields) -> dict | None:
        allowed = {"user_label", "user_note", "label", "part", "function", "confidence"}
        sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "check" in fields and fields["check"] is not None:
            sets["chk"] = fields["check"]
        if "box" in fields and fields["box"] is not None:
            sets["box"] = json.dumps(fields["box"])
        if sets:
            cols = ", ".join(f"{k} = %s" for k in sets)
            with self._conn.cursor() as cur:
                cur.execute(
                    f"UPDATE pcb_component SET {cols} WHERE id = %s", (*sets.values(), comp_id))
        row = self._one("SELECT * FROM pcb_component WHERE id = %s", (comp_id,))
        return self._pcb_row(row) if row else None
