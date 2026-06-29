"""FastAPI app: local wiring-diagram vision + chat server.

Serves an attractive single-page UI and a small JSON API. All inference runs against a
local Ollama model; all data (diagrams, VINs, memories) stays on this machine.
"""

from __future__ import annotations

import base64
import json
import os
import re
import threading
import time
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from canopy.hal.instruments import InstrumentHub
from canopy.profiles import generate as profile_generate
from canopy.profiles.schema import ModuleProfile
from canopy.vision import auth, extract, productlib
from canopy.vision import bench as benchmod
from canopy.vision import diagram as dg
from canopy.vision import knowledge as kb
from canopy.vision import research as researchmod
from canopy.vision import wiki as wikimod
from canopy.vision.api_reference import API_REFERENCE
from canopy.vision.config import VisionConfig
from canopy.vision.ollama_client import ChatMessage, OllamaClient, OllamaError
from canopy.vision.prompts import RESEARCH_SYSTEM
from canopy.vision.store import make_store

STATIC_DIR = Path(__file__).parent / "static"


# --- request bodies -----------------------------------------------------------
class VehicleBody(BaseModel):
    vin: str = ""
    year: str = ""
    make: str = ""
    model: str = ""
    label: str = ""


class MemoryBody(BaseModel):
    content: str
    kind: str = "note"


class ChatBody(BaseModel):
    message: str
    save_memories: bool = False
    page: int = 0


class ExtractBody(BaseModel):
    page: int = 0
    all_pages: bool = False


class TagBody(BaseModel):
    tag: str


class LoginBody(BaseModel):
    username: str = ""
    password: str = ""
    secure: bool = False


class UserBody(BaseModel):
    username: str = ""
    password: str = ""
    role: str = "user"  # admin | user


class AccessBody(BaseModel):
    vehicle_id: int
    level: str = "read"  # read | write | none


class OrgBody(BaseModel):
    name: str | None = None
    color: str | None = None
    x: float | None = None
    y: float | None = None


class AssignBody(BaseModel):
    user_id: int
    org_id: int | None = None  # None -> unassign (free agent)


class AssistantBody(BaseModel):
    message: str
    history: list[dict] = []


class ConnectBody(BaseModel):
    interface: str = "socketcan"
    channel: str = "can0"
    bitrate: int = 500000
    fd: bool = False


class SendFrameBody(BaseModel):
    id: str
    data: str = ""
    extended: bool = False


class UdsBody(BaseModel):
    request_id: str = "0x7E0"
    response_id: str = "0x7E8"
    payload: str = ""  # hex, e.g. "22F190"


class PingBody(BaseModel):
    request_id: str = "0x7E0"
    response_id: str = "0x7E8"


class RestbusBody(BaseModel):
    messages: list[str] = []  # subset of DBC message names; empty = all periodic


class InstrConnectBody(BaseModel):
    source: str = ""  # '' = simulated; serial port; or a VISA resource (USB::...::INSTR)
    port: str = ""    # legacy alias


class MeasurementBody(BaseModel):
    kind: str = "dmm"            # dmm | scope
    label: str = ""
    mode: str = ""               # vdc / scope channel / ...
    value: float | None = None   # the numeric reading (DMM)
    unit: str = ""
    data: object | None = None   # e.g. scope samples (stored as JSON)
    note: str = ""
    image: str = ""              # base64 PNG (scope capture) -> saved as an attachment


class SigGenBody(BaseModel):
    waveform: str | None = None
    freq_hz: float | None = None
    amp_vpp: float | None = None
    offset_v: float | None = None
    duty: float | None = None
    enabled: bool | None = None


class ResearchBody(BaseModel):
    query: str
    synthesize: bool = True


class TriageBody(BaseModel):
    message: str
    image: str = ""  # optional base64 (data URL or raw) of a board/scope/meter photo
    history: list[dict] = []


class PcbBody(BaseModel):
    image: str  # base64 (data URL or raw) of the PCB photo
    note: str = ""


class PcbComponentUpdate(BaseModel):
    user_label: str | None = None  # tech's corrected name for the part
    user_note: str | None = None   # spec / correction / observation for the record
    label: str | None = None
    part: str | None = None
    function: str | None = None
    check: str | None = None
    box: list[float] | None = None  # [x0,y0,x1,y1] fractions, after move/resize


class PcbComponentNew(BaseModel):
    attachment_id: int | None = None
    label: str = "New component"
    part: str = ""
    box: list[float] = [0.4, 0.4, 0.6, 0.6]
    function: str = ""
    check: str = ""
    identify: bool = True  # ask the model for function + what-to-check


class PcbIdentifyBody(BaseModel):
    label: str
    part: str = ""


class AttachmentUpdate(BaseModel):
    note: str = ""  # caption / annotation for the image (for the wiki)


class AnnotationBody(BaseModel):
    image: str       # base64 PNG of the flattened (image + drawn markup) annotation
    note: str = ""   # caption


class ProfileBody(BaseModel):
    yaml: str


class GuidedNextBody(BaseModel):
    phase: str = "intake"
    symptom: str = ""


class GuidedStepBody(BaseModel):
    phase: str
    title: str
    result: str = ""
    status: str = "note"  # pass | fail | note | finding


class IntegrationBody(BaseModel):
    name: str = ""
    kind: str = "rest"
    base_url: str = ""
    auth_type: str = "none"        # none | api_key | bearer | basic
    config: dict | None = None     # e.g. {header_name, key_in, param_name, username}
    secret: str | None = None      # token / key / password (write-only)
    enabled: bool | None = True


# Extensible connector presets — most "integrations" are just (base URL + auth) over REST.
INTEGRATION_PRESETS = [
    {"kind": "slack", "label": "Slack", "base_url": "https://slack.com/api",
     "auth_type": "bearer", "hint": "Bot token (xoxb-…), or use an Incoming Webhook URL."},
    {"kind": "gdrive", "label": "Google Drive", "base_url": "https://www.googleapis.com/drive/v3",
     "auth_type": "bearer", "hint": "OAuth access token (or service-account bearer)."},
    {"kind": "monday", "label": "Monday.com", "base_url": "https://api.monday.com/v2",
     "auth_type": "api_key", "config": {"header_name": "Authorization"},
     "hint": "API token sent in the Authorization header."},
    {"kind": "digikey", "label": "Digi-Key", "base_url": "https://api.digikey.com",
     "auth_type": "bearer", "hint": "OAuth2 client-credentials token (client id/secret → token)."},
    {"kind": "mouser", "label": "Mouser", "base_url": "https://api.mouser.com/api/v1",
     "auth_type": "api_key", "config": {"key_in": "query", "param_name": "apiKey"},
     "hint": "API key passed as ?apiKey=…"},
    {"kind": "wordpress", "label": "WordPress", "base_url": "https://YOURSITE/wp-json/wp/v2",
     "auth_type": "basic", "config": {"username": ""},
     "hint": "Username + Application Password (HTTP Basic)."},
    {"kind": "dropbox", "label": "Dropbox", "base_url": "https://api.dropboxapi.com/2",
     "auth_type": "bearer", "hint": "OAuth access token."},
    {"kind": "rest", "label": "Generic REST API", "base_url": "", "auth_type": "none",
     "hint": "Any REST API — set the base URL and pick the auth method."},
]


def _parse_id(v: str) -> int:
    v = v.strip()
    return int(v, 16) if v.lower().startswith("0x") else int(v, 16)


def _pinout_text(pinouts: list[dict]) -> str:
    if not pinouts:
        return "(no pinout extracted yet)"
    lines = ["connector | pin | signal | function | circuit | wire_color | connects_to"]
    for p in pinouts:
        lines.append(
            f"{p.get('connector','')} | {p.get('pin','')} | {p.get('signal','')} | "
            f"{p.get('function','')} | {p.get('circuit','')} | {p.get('wire_color','')} | "
            f"{p.get('connects_to','')}"
        )
    return "\n".join(lines)




def create_app(config: VisionConfig | None = None) -> FastAPI:
    config = config or VisionConfig.from_env()
    config.ensure_dirs()

    app = FastAPI(title="CANOPY Vision", docs_url="/api/docs")
    app.add_middleware(GZipMiddleware, minimum_size=600)  # compress JSON/HTML/JS
    secret = auth.load_secret(config.data_dir)
    store = make_store(config)

    # Bootstrap the admin account from CANOPY_PASSWORD on first run. With no users
    # and no password we stay in "open mode" (local/dev, no login) for backward compat.
    if store.count_users() == 0 and config.password:
        store.create_user("admin", auth.hash_password(config.password), "admin")
    open_mode = store.count_users() == 0
    LOCAL_ADMIN = {"id": 0, "username": "local", "role": "admin"}
    ADMIN_PATHS = ("/api/integrations", "/api/users", "/api/orgs")
    PUBLIC_PATHS = ("/login", "/api/login", "/healthz", "/m", "/favicon.ico")
    _VID_RE = re.compile(r"^/api/vehicles/(\d+)")

    def _deny(path: str, code: int, msg: str):
        if path.startswith("/api"):
            return JSONResponse(status_code=code, content={"detail": msg})
        return RedirectResponse("/login" if code == 401 else "/")

    @app.middleware("http")
    async def require_auth(request, call_next):
        path = request.url.path
        if (path in PUBLIC_PATHS or path.startswith("/static")
                or path.startswith("/api/pair/")):
            return await call_next(request)
        if open_mode:
            request.state.user = LOCAL_ADMIN
            return await call_next(request)
        uid = auth.valid_token(secret, request.cookies.get(auth.COOKIE))
        user = store.get_user(uid) if uid else None
        if not user:
            return _deny(path, 401, "unauthorized")
        request.state.user = user
        is_admin = user["role"] == "admin"
        # admin-only console + management APIs
        if (path == "/admin" or path.startswith(ADMIN_PATHS)) and not is_admin:
            return _deny(path, 403, "admin only")
        # per-project read/write access for sub-users
        if not is_admin:
            m = _VID_RE.match(path)
            if m:
                lvl = store.access_level(user["id"], int(m.group(1)))
                if lvl is None:
                    return _deny(path, 403, "no access to this project")
                if request.method in ("POST", "PUT", "PATCH", "DELETE") and lvl != "write":
                    return _deny(path, 403, "read-only access to this project")
        return await call_next(request)

    def current_user(request: Request) -> dict:
        return getattr(request.state, "user", None) or LOCAL_ADMIN

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.get("/favicon.ico")
    def favicon() -> FileResponse:
        return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")

    @app.get("/login")
    def login_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "login.html")

    @app.post("/api/login")
    def login(body: LoginBody) -> JSONResponse:
        if open_mode:
            return JSONResponse({"ok": True, "user": {"username": "local", "role": "admin"}})
        user = store.get_user_by_username(body.username)
        if user and auth.verify_password(user["password_hash"], body.password):
            resp = JSONResponse(
                {"ok": True, "user": {"username": user["username"], "role": user["role"]}})
            resp.set_cookie(auth.COOKIE, auth.make_token(secret, user["id"]), httponly=True,
                            samesite="lax", max_age=auth.TTL, secure=body.secure)
            return resp
        return JSONResponse(status_code=401, content={"detail": "invalid username or password"})

    @app.post("/api/logout")
    def logout() -> JSONResponse:
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(auth.COOKIE)
        return resp

    @app.get("/api/auth/status")
    def auth_status(request: Request) -> dict:
        u = current_user(request)
        team = store.team_of_user(u["id"]) if u.get("id") else None
        return {"auth": not open_mode, "open_mode": open_mode,
                "user": {"id": u["id"], "username": u["username"], "role": u["role"]},
                "team": _team_brief(team)}

    def _team_brief(team: dict | None) -> dict | None:
        return {"id": team["id"], "name": team["name"], "color": team["color"]} if team else None

    # --- user management (admin-only; enforced in middleware) ---
    def _user_public(u: dict) -> dict:
        return {"id": u["id"], "username": u["username"], "role": u["role"],
                "created_at": u.get("created_at", ""), "projects": u.get("projects", 0)}

    @app.get("/api/users")
    def users_list() -> list[dict]:
        return store.list_users()

    @app.post("/api/users")
    def users_create(body: UserBody) -> dict:
        if not body.username or not body.password:
            raise HTTPException(400, "username and password are required")
        if store.get_user_by_username(body.username):
            raise HTTPException(409, "that username is taken")
        role = "admin" if body.role == "admin" else "user"
        u = store.create_user(body.username, auth.hash_password(body.password), role)
        return _user_public(u)

    @app.delete("/api/users/{uid}")
    def users_delete(uid: int, request: Request) -> dict:
        if uid == current_user(request)["id"]:
            raise HTTPException(400, "you can't delete your own account")
        target = store.get_user(uid)
        if target and target["role"] == "admin":
            admins = sum(1 for u in store.list_users() if u["role"] == "admin")
            if admins <= 1:
                raise HTTPException(400, "can't delete the last admin")
        store.delete_user(uid)
        return {"ok": True}

    @app.get("/api/users/{uid}/access")
    def users_access(uid: int) -> dict:
        return store.access_map(uid)

    @app.put("/api/users/{uid}/access")
    def users_set_access(uid: int, body: AccessBody) -> dict:
        store.set_access(uid, body.vehicle_id, body.level)
        return store.access_map(uid)

    # --- organizations / teams (admin-only; bubble UI) ---
    @app.get("/api/orgs")
    def orgs_list() -> list[dict]:
        return store.list_orgs()

    @app.post("/api/orgs")
    def orgs_create(body: OrgBody) -> dict:
        return store.create_org(name=(body.name or "New team"),
                                color=(body.color or "#0f9d6b"), x=body.x, y=body.y)

    @app.post("/api/orgs/assign")  # registered before /{oid} so "assign" isn't read as an id
    def orgs_assign(body: AssignBody) -> dict:
        store.assign_org(body.user_id, body.org_id)
        return {"ok": True}

    @app.put("/api/orgs/{oid}")
    def orgs_update(oid: int, body: OrgBody) -> dict:
        row = store.update_org(oid, **body.model_dump(exclude_none=True))
        if not row:
            raise HTTPException(404, "no such organization")
        return row

    @app.delete("/api/orgs/{oid}")
    def orgs_delete(oid: int) -> dict:
        store.delete_org(oid)
        return {"ok": True}

    def _apply_team_access(oid: int, vehicle_id: int, level: str) -> None:
        """Grant/revoke a whole team's access to one project (and tag project ownership)."""
        org = store.get_org(oid)
        members = org["members"] if org else []
        if level in (None, "", "none"):
            for m in members:
                store.set_access(m, vehicle_id, "none")
            store.set_project_team(vehicle_id, None)
        else:
            for m in members:
                store.set_access(m, vehicle_id, level)
            store.set_project_team(vehicle_id, oid, level)

    @app.get("/api/orgs/{oid}/access")
    def orgs_access_get(oid: int) -> dict:
        return store.org_access_map(oid)

    @app.put("/api/orgs/{oid}/access")
    def orgs_access_set(oid: int, body: AccessBody) -> dict:
        _apply_team_access(oid, body.vehicle_id, body.level)
        return store.org_access_map(oid)
    client = OllamaClient(
        config.ollama_url, config.model, timeout=config.request_timeout
    )

    if os.environ.get("CANOPY_WARM", "1") != "0" and not os.environ.get("PYTEST_CURRENT_TEST"):
        # Best-effort: preload the model so the first triage/guided call isn't a cold start.
        def _warm() -> None:
            try:
                client.chat([ChatMessage("user", "ok")], temperature=0.0)
            except Exception:
                pass
        threading.Thread(target=_warm, daemon=True).start()

    image_cache: dict[tuple[int, int], list[str]] = {}

    def page_image(vehicle_id: int, page: int) -> list[str]:
        d = store.latest_diagram(vehicle_id)
        if d is None:
            return []
        key = (d["id"], page)
        if key not in image_cache:
            image_cache[key] = dg.b64_page(Path(d["path"]), d["mime"], page)
        return image_cache[key]

    def page_text(vehicle_id: int, page: int) -> str:
        d = store.latest_diagram(vehicle_id)
        if d is None:
            return ""
        return dg.page_text(Path(d["path"]), d["mime"], page)

    def embed(text: str) -> list[float]:
        try:
            return client.embed(text, model=config.embed_model)
        except OllamaError:
            return []

    def save_memory_if_novel(vehicle_id: int, content: str, kind: str) -> dict | None:
        """Embed + store a memory only if it isn't a near-duplicate of an existing one."""
        existing = store.list_memories(vehicle_id)
        vec = embed(content)
        if vec and not extract.is_novel(vec, [m["embedding"] for m in existing if m["embedding"]]):
            return None
        return store.add_memory(vehicle_id, content, kind=kind, embedding=vec or None)

    def relevant_memories(vehicle_id: int, question: str, k: int = 6) -> list[str]:
        """Top-k memories most semantically relevant to the question (else most recent)."""
        qvec = embed(question)
        if qvec and hasattr(store, "search_memories"):  # server-side pgvector ANN
            return [m["content"] for m in store.search_memories(qvec, k=k, vehicle_id=vehicle_id)]
        mems = store.list_memories(vehicle_id)
        have_vecs = [(m["embedding"], m["content"]) for m in mems if m["embedding"]]
        if qvec and have_vecs:
            ranked = extract.rank_by_similarity(qvec, have_vecs, k=k)
            extras = [m["content"] for m in mems if not m["embedding"]][: max(0, k - len(ranked))]
            return ranked + extras
        return [m["content"] for m in mems][:k]

    def chat_context(vehicle_id: int, question: str) -> str:
        v = store.get_vehicle(vehicle_id)
        ident = " ".join(filter(None, [v["year"], v["make"], v["model"]])) or "(unidentified)"
        tags = ", ".join(store.list_tags(vehicle_id)) or "(none)"
        mems = relevant_memories(vehicle_id, question)
        return "\n\n".join([
            f"PROJECT: {ident}  VIN: {v['vin'] or '(unknown)'}  TAGS: {tags}",
            "RELEVANT MEMORIES:\n" + ("\n".join(f"- {m}" for m in mems) if mems else "- (none)"),
            "EXTRACTED PINOUT:\n" + _pinout_text(store.list_pinouts(vehicle_id)),
        ])

    # --- health & static -------------------------------------------------------
    @app.get("/api/health")
    def health() -> dict:
        try:
            models = client.list_models()
            ok = config.model in models
        except OllamaError:
            models, ok = [], False
        return {
            "ollama_url": config.ollama_url,
            "model": config.model,
            "model_ready": ok,
            "models": models,
        }

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    # --- vehicles --------------------------------------------------------------
    @app.get("/api/vehicles")
    def list_vehicles(request: Request) -> list[dict]:
        u = current_user(request)
        vs = store.list_vehicles()
        if u["role"] == "admin":
            return vs
        acc = store.access_map(u["id"])
        return [v for v in vs if v["id"] in acc]

    @app.post("/api/vehicles")
    def create_vehicle(body: VehicleBody, request: Request) -> dict:
        v = store.create_vehicle(**body.model_dump())
        u = current_user(request)
        if u["role"] != "admin" and u["id"]:  # creator gets write access to their project
            store.set_access(u["id"], v["id"], "write")
        return v

    @app.get("/api/vehicles/{vehicle_id}")
    def get_vehicle(vehicle_id: int) -> dict:
        try:
            v = store.get_vehicle(vehicle_id)
        except KeyError:
            raise HTTPException(404, "vehicle not found") from None
        v["diagrams"] = store.list_diagrams(vehicle_id)
        v["pinouts"] = store.list_pinouts(vehicle_id)
        v["memories"] = store.list_memories(vehicle_id)
        v["messages"] = store.list_messages(vehicle_id)
        v["tags"] = store.list_tags(vehicle_id)
        return v

    @app.patch("/api/vehicles/{vehicle_id}")
    def update_vehicle(vehicle_id: int, body: VehicleBody) -> dict:
        return store.update_vehicle(vehicle_id, **body.model_dump())

    @app.delete("/api/vehicles/{vehicle_id}")
    def delete_vehicle(vehicle_id: int) -> dict:
        store.delete_vehicle(vehicle_id)
        return {"ok": True}

    # --- diagrams --------------------------------------------------------------
    @app.post("/api/vehicles/{vehicle_id}/diagram")
    async def upload_diagram(vehicle_id: int, file: UploadFile) -> dict:
        data = await file.read()
        path = dg.save_upload(config.uploads_dir, vehicle_id, file.filename or "diagram", data)
        mime = file.content_type or "application/octet-stream"
        pages = dg.page_count(path, mime)
        rec = store.add_diagram(
            vehicle_id, filename=file.filename or path.name, path=str(path), mime=mime, pages=pages
        )
        image_cache.pop(rec["id"], None)
        return rec

    @app.get("/api/diagram/{diagram_id}/image")
    def diagram_image(diagram_id: int, page: int = 0) -> Response:
        try:
            d = store.get_diagram(diagram_id)
        except KeyError:
            raise HTTPException(404, "diagram not found") from None
        png = dg.render_page(Path(d["path"]), d["mime"], page)
        return Response(content=png, media_type="image/png")

    # --- AI actions ------------------------------------------------------------
    def _require_page(vehicle_id: int, page: int) -> list[str]:
        imgs = page_image(vehicle_id, page)
        if not imgs:
            raise HTTPException(400, "upload a diagram first")
        return imgs

    @app.post("/api/vehicles/{vehicle_id}/extract")
    def extract_pinout(vehicle_id: int, body: ExtractBody) -> dict:
        d = store.latest_diagram(vehicle_id)
        if d is None:
            raise HTTPException(400, "upload a diagram first")
        did = d["id"]
        pages = range(d["pages"]) if body.all_pages else [body.page]
        connectors: list[str] = []
        try:
            for page in pages:
                imgs = page_image(vehicle_id, page)
                result = extract.extract_pinout(client, imgs, page_text(vehicle_id, page))
                if result["pins"]:
                    store.merge_pinouts(vehicle_id, did, page, result["pins"])
                    connectors += result["connectors"]
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        return {
            "connectors": sorted(set(connectors)),
            "pinouts": store.list_pinouts(vehicle_id),
            "pages_scanned": len(list(pages)),
        }

    @app.post("/api/vehicles/{vehicle_id}/identify")
    def identify_vehicle(vehicle_id: int, body: ExtractBody) -> dict:
        imgs = _require_page(vehicle_id, body.page)
        try:
            ident = extract.identify_vehicle(client, imgs)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        return store.update_vehicle(
            vehicle_id,
            vin=ident.get("vin") or None,
            year=ident.get("year") or None,
            make=ident.get("make") or None,
            model=ident.get("model") or None,
        )

    @app.post("/api/vehicles/{vehicle_id}/can-plan")
    def can_plan(vehicle_id: int, body: ExtractBody) -> dict:
        imgs = _require_page(vehicle_id, body.page)
        text = _pinout_text(store.list_pinouts(vehicle_id))
        try:
            plan = extract.can_bench_plan(client, text, imgs)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        return {"plan": plan}

    # --- pinouts / memories ----------------------------------------------------
    @app.get("/api/vehicles/{vehicle_id}/pinouts")
    def list_pinouts(vehicle_id: int) -> list[dict]:
        return store.list_pinouts(vehicle_id)

    @app.get("/api/vehicles/{vehicle_id}/memories")
    def list_memories(vehicle_id: int) -> list[dict]:
        return store.list_memories(vehicle_id)

    @app.post("/api/vehicles/{vehicle_id}/memories")
    def add_memory(vehicle_id: int, body: MemoryBody) -> dict:
        return store.add_memory(
            vehicle_id, body.content, kind=body.kind, embedding=embed(body.content) or None
        )

    @app.delete("/api/memories/{memory_id}")
    def delete_memory(memory_id: int) -> dict:
        store.delete_memory(memory_id)
        return {"ok": True}

    # --- tags ------------------------------------------------------------------
    @app.get("/api/vehicles/{vehicle_id}/tags")
    def list_tags(vehicle_id: int) -> list[str]:
        return store.list_tags(vehicle_id)

    @app.post("/api/vehicles/{vehicle_id}/tags")
    def add_tag(vehicle_id: int, body: TagBody) -> list[str]:
        return store.add_tag(vehicle_id, body.tag)

    @app.delete("/api/vehicles/{vehicle_id}/tags/{tag}")
    def remove_tag(vehicle_id: int, tag: str) -> list[str]:
        return store.remove_tag(vehicle_id, tag)

    @app.post("/api/vehicles/{vehicle_id}/extract-tags")
    def extract_tags(vehicle_id: int, body: ExtractBody) -> dict:
        imgs = _require_page(vehicle_id, body.page)
        v = store.get_vehicle(vehicle_id)
        ident = " ".join(filter(None, [v["year"], v["make"], v["model"], v["label"]]))
        try:
            tags = extract.extract_tags(client, imgs, ident)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        for t in tags:
            store.add_tag(vehicle_id, t)
        return {"tags": store.list_tags(vehicle_id)}

    @app.post("/api/vehicles/{vehicle_id}/suggest")
    def suggest(vehicle_id: int, body: ExtractBody) -> dict:
        """AI first-attempt at project identity + name + tags (does NOT commit)."""
        imgs = _require_page(vehicle_id, body.page)
        try:
            ident = extract.identify_vehicle(client, imgs)
            seed = " ".join(filter(None, [ident.get("year"), ident.get("make"),
                                          ident.get("model"), ident.get("engine"),
                                          ident.get("module_type")]))
            tags = extract.extract_tags(client, imgs, seed)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        label = " ".join(filter(None, [ident.get("year"), ident.get("make"),
                                       ident.get("model"), ident.get("module_type")])).strip()
        return {**ident, "label": label or "Untitled project", "tags": tags}

    @app.post("/api/vehicles/{vehicle_id}/extract-memories")
    def extract_memories(vehicle_id: int, body: ExtractBody) -> dict:
        """Distil durable facts about the project from identity + pinout + page text."""
        v = store.get_vehicle(vehicle_id)
        ident = " ".join(filter(None, [v["year"], v["make"], v["model"]]))
        transcript = (
            f"Vehicle: {ident}\nConnector pinout:\n{_pinout_text(store.list_pinouts(vehicle_id))}"
            f"\nDiagram page text:\n{page_text(vehicle_id, body.page)[:2000]}"
        )
        try:
            candidates = extract.suggest_memories(client, transcript)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        existing = [m["content"] for m in store.list_memories(vehicle_id)]
        saved = [f for f in extract.dedup_memories(candidates, existing)
                 if save_memory_if_novel(vehicle_id, f, "auto")]
        return {"memories": saved}

    # --- chat ------------------------------------------------------------------
    @app.post("/api/vehicles/{vehicle_id}/chat")
    def chat(vehicle_id: int, body: ChatBody) -> dict:
        imgs = page_image(vehicle_id, body.page)
        context = chat_context(vehicle_id, body.message)
        ptext = page_text(vehicle_id, body.page)
        if ptext:
            context += f"\n\nCURRENT PAGE ({body.page + 1}) TEXT LAYER:\n{ptext}"
        history = [
            ChatMessage(m["role"], m["content"])
            for m in store.list_messages(vehicle_id)
            if m["role"] in ("user", "assistant")
        ][-8:]
        store.add_message(vehicle_id, "user", body.message)
        try:
            reply = extract.chat_about_diagram(
                client, body.message, context=context, history=history, images=imgs
            )
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        store.add_message(vehicle_id, "assistant", reply)

        saved = _auto_memories(vehicle_id, body.message, reply) if body.save_memories else []
        return {"reply": reply, "saved_memories": saved}

    def _auto_memories(vehicle_id: int, question: str, answer: str) -> list[str]:
        """Distil new, salient, non-duplicate facts and save them (kind='auto').

        Two-stage dedup: a cheap text-similarity gate, then a semantic embedding gate so
        we don't accumulate restatements of the same fact.
        """
        transcript = f"Q: {question}\nA: {answer}"
        try:
            candidates = extract.suggest_memories(client, transcript)
        except OllamaError:
            return []
        existing = [m["content"] for m in store.list_memories(vehicle_id)]
        saved = []
        for fact in extract.dedup_memories(candidates, existing):
            if save_memory_if_novel(vehicle_id, fact, "auto"):
                saved.append(fact)
        return saved

    @app.post("/api/vehicles/{vehicle_id}/chat/stream")
    def chat_stream(vehicle_id: int, body: ChatBody) -> StreamingResponse:
        imgs = page_image(vehicle_id, body.page)
        context = chat_context(vehicle_id, body.message)
        ptext = page_text(vehicle_id, body.page)
        if ptext:
            context += f"\n\nCURRENT PAGE ({body.page + 1}) TEXT LAYER:\n{ptext}"
        history = [
            ChatMessage(m["role"], m["content"])
            for m in store.list_messages(vehicle_id)
            if m["role"] in ("user", "assistant")
        ][-8:]
        store.add_message(vehicle_id, "user", body.message)

        def event_stream():
            parts: list[str] = []
            try:
                for chunk in extract.chat_about_diagram_stream(
                    client, body.message, context=context, history=history, images=imgs
                ):
                    parts.append(chunk)
                    yield f"event: token\ndata: {json.dumps(chunk)}\n\n"
            except OllamaError as e:
                yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
                return
            reply = "".join(parts)
            store.add_message(vehicle_id, "assistant", reply)
            saved = _auto_memories(vehicle_id, body.message, reply) if body.save_memories else []
            yield f"event: done\ndata: {json.dumps({'saved_memories': saved})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/api/reference")
    def api_reference() -> dict:
        """Curated endpoint reference for the in-app API docs (also see /api/docs)."""
        return {"openapi": "/openapi.json", "swagger": "/api/docs", "groups": API_REFERENCE}

    # --- global cross-vehicle assistant ----------------------------------------
    def assistant_context(question: str, k: int = 10) -> str:
        qvec = embed(question)
        if qvec and hasattr(store, "search_memories"):  # server-side pgvector ANN
            chosen = store.search_memories(qvec, k=k)
        else:
            mems = store.all_memories()
            have = [(m["embedding"], m) for m in mems if m["embedding"]]
            chosen = extract.rank_by_similarity(qvec, have, k=k) if (qvec and have) else mems[:k]
        lines = [f"- [{m['project']}] {m['content']}" for m in chosen]
        projects = store.list_vehicles()
        summary = ", ".join(
            f"{v['label'] or 'project'} ({', '.join(v.get('tags', [])[:4])})" for v in projects[:12]
        )
        return (
            kb.context_block(question) + "\n\n"
            f"KNOWN PROJECTS: {summary or '(none yet)'}\n\n"
            f"RELEVANT ACCUMULATED MEMORIES:\n" + ("\n".join(lines) if lines else "- (none yet)")
        )

    @app.post("/api/assistant/chat/stream")
    def assistant_stream(body: AssistantBody) -> StreamingResponse:
        context = assistant_context(body.message)
        history = [
            ChatMessage(m.get("role", "user"), m.get("content", ""))
            for m in body.history if m.get("role") in ("user", "assistant")
        ][-8:]

        def gen():
            parts: list[str] = []
            try:
                for chunk in extract.assistant_stream(
                    client, body.message, context=context, history=history
                ):
                    parts.append(chunk)
                    yield f"event: token\ndata: {json.dumps(chunk)}\n\n"
            except OllamaError as e:
                yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
                return
            yield f"event: done\ndata: {json.dumps({})}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    # --- guided repair triage (multimodal: board/scope photos) -----------------
    def _decode_b64_image(raw: str) -> str:
        """Return bare base64 image bytes for an image given as a data URL, raw base64, or an
        ``/api/attachment/{id}/image`` reference (the PCB 'Send to Triage' path passes the latter,
        which must NOT be base64-decoded as-is — that yields garbage Ollama rejects)."""
        s = (raw or "").strip()
        m = re.search(r"/api/attachment/(\d+)/image", s)
        if m:
            att = store.get_attachment(int(m.group(1)))
            if att and Path(att["path"]).exists():
                return base64.b64encode(Path(att["path"]).read_bytes()).decode()
            raise HTTPException(400, "referenced image not found")
        return s.split(",", 1)[1] if s.startswith("data:") else s

    def _clean_image_b64(raw: str) -> str:
        """Decode + re-encode an image to a clean PNG so the model never gets an unknown format;
        raises 400 (not a downstream 500) if the bytes aren't a valid image."""
        b64 = _decode_b64_image(raw)
        try:
            return base64.b64encode(dg._downscale_png(base64.b64decode(b64))).decode()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, "unsupported or corrupt image") from e

    @app.get("/api/vehicles/{vehicle_id}/triage/messages")
    def triage_messages(vehicle_id: int) -> list[dict]:
        return store.list_messages(vehicle_id, channel="triage")

    @app.post("/api/vehicles/{vehicle_id}/triage/stream")
    def triage_stream(vehicle_id: int, body: TriageBody) -> StreamingResponse:
        context = kb.context_block(body.message) + "\n\n" + chat_context(vehicle_id, body.message)
        history = [
            ChatMessage(m.get("role", "user"), m.get("content", ""))
            for m in body.history if m.get("role") in ("user", "assistant")
        ][-8:]
        images: list[str] = []
        note = body.message
        if body.image:
            b64 = _clean_image_b64(body.image)  # valid PNG, resolves attachment URLs
            images = [b64]
            try:
                path = config.uploads_dir / f"v{vehicle_id}_triage_{int(time.time() * 1000)}.png"
                path.write_bytes(base64.b64decode(b64))
                att = store.add_attachment(
                    vehicle_id, str(path), kind="photo", note=body.message[:200])
                # Embed the saved image so the transcript keeps the photo across reloads.
                note = f"{body.message}\n\n![photo](/api/attachment/{att['id']}/image)".strip()
            except (ValueError, OSError):
                pass
        store.add_message(vehicle_id, "user", note, channel="triage")

        def gen():
            parts: list[str] = []
            try:
                for chunk in extract.triage_stream(
                    client, body.message, context=context, history=history, images=images
                ):
                    parts.append(chunk)
                    yield f"event: token\ndata: {json.dumps(chunk)}\n\n"
            except OllamaError as e:
                yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
                return
            store.add_message(vehicle_id, "assistant", "".join(parts), channel="triage")
            yield f"event: done\ndata: {json.dumps({})}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/vehicles/{vehicle_id}/pcb")
    def pcb_analyze(vehicle_id: int, body: PcbBody) -> dict:
        b64 = _decode_b64_image(body.image)
        small_b64 = b64
        attachment_id: int | None = None
        try:
            raw = base64.b64decode(b64)
            path = config.uploads_dir / f"v{vehicle_id}_pcb_{int(time.time() * 1000)}.png"
            path.write_bytes(raw)
            att = store.add_attachment(vehicle_id, str(path), kind="pcb", note=body.note[:200])
            attachment_id = att["id"]
            small_b64 = base64.b64encode(dg._downscale_png(raw)).decode()  # speed up inference
        except (ValueError, OSError):
            pass
        v = store.get_vehicle(vehicle_id)
        ident = " ".join(filter(None, [v["year"], v["make"], v["model"], v["label"]]))
        pins = _pinout_text(store.list_pinouts(vehicle_id))
        ctx = f"Module: {ident or '(unidentified)'}\nPinout:\n{pins}"
        try:
            result = extract.analyze_pcb(client, [small_b64], ctx)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        # Persist the boxed parts so they survive reloads and can be corrected by the tech.
        stored = store.replace_pcb_components(vehicle_id, attachment_id, result["components"])
        if stored:
            summary = "PCB components identified: " + ", ".join(
                c["label"] for c in stored[:12] if c["label"]
            )
            save_memory_if_novel(vehicle_id, summary, "pcb")  # retain for cross-module recall
        return {"components": stored, "attachment_id": attachment_id}

    @app.get("/api/vehicles/{vehicle_id}/pcb-photos")
    def pcb_photos(vehicle_id: int) -> list[dict]:
        return store.list_pcb_photos(vehicle_id)

    @app.get("/api/vehicles/{vehicle_id}/pcb-components")
    def pcb_components(vehicle_id: int, attachment_id: int | None = None) -> dict:
        att = attachment_id
        if att is None:
            att = store.latest_pcb_attachment(vehicle_id)
        comps = store.list_pcb_components(vehicle_id, att) if att is not None else []
        return {"components": comps, "attachment_id": att,
                "photos": store.list_pcb_photos(vehicle_id)}

    @app.post("/api/vehicles/{vehicle_id}/pcb-component")
    def pcb_component_add(vehicle_id: int, body: PcbComponentNew) -> dict:
        function, check = body.function, body.check
        if body.identify and not (function and check):
            v = store.get_vehicle(vehicle_id)
            ident = " ".join(filter(None, [v["year"], v["make"], v["model"], v["label"]]))
            ctx = f"Module: {ident or '(unidentified)'}\nPinout:\n" \
                  f"{_pinout_text(store.list_pinouts(vehicle_id))}"
            try:
                got = extract.identify_component(client, body.label, body.part, ctx)
                function = function or got["function"]
                check = check or got["check"]
            except OllamaError:
                pass
        return store.add_pcb_component(vehicle_id, body.attachment_id, {
            "label": body.label, "part": body.part, "box": body.box,
            "function": function, "check": check, "confidence": 0.0,
        })

    @app.post("/api/vehicles/{vehicle_id}/pcb-component/identify")
    def pcb_component_identify(vehicle_id: int, body: PcbIdentifyBody) -> dict:
        v = store.get_vehicle(vehicle_id)
        ident = " ".join(filter(None, [v["year"], v["make"], v["model"], v["label"]]))
        ctx = f"Module: {ident or '(unidentified)'}\nPinout:\n" \
              f"{_pinout_text(store.list_pinouts(vehicle_id))}"
        try:
            return extract.identify_component(client, body.label, body.part, ctx)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e

    @app.patch("/api/pcb-component/{comp_id}")
    def pcb_component_update(comp_id: int, body: PcbComponentUpdate) -> dict:
        row = store.update_pcb_component(
            comp_id, user_label=body.user_label, user_note=body.user_note,
            label=body.label, part=body.part, function=body.function,
            check=body.check, box=body.box,
        )
        if row is None:
            raise HTTPException(404, "component not found")
        return row

    @app.delete("/api/pcb-component/{comp_id}")
    def pcb_component_delete(comp_id: int) -> dict:
        store.delete_pcb_component(comp_id)
        return {"ok": True}

    # --- Admin Console: third-party integrations -------------------------------
    @app.get("/admin")
    def admin_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "admin.html")

    @app.get("/api/integrations/presets")
    def integration_presets() -> list[dict]:
        return INTEGRATION_PRESETS

    @app.get("/api/integrations")
    def integrations_list() -> list[dict]:
        return store.list_integrations()

    @app.post("/api/integrations")
    def integration_add(body: IntegrationBody) -> dict:
        return store.add_integration(**body.model_dump())

    @app.put("/api/integrations/{integ_id}")
    def integration_update(integ_id: int, body: IntegrationBody) -> dict:
        row = store.update_integration(integ_id, **body.model_dump(exclude_none=True))
        if not row:
            raise HTTPException(404, "no such integration")
        return row

    @app.delete("/api/integrations/{integ_id}")
    def integration_delete(integ_id: int) -> dict:
        store.delete_integration(integ_id)
        return {"ok": True}

    @app.post("/api/integrations/{integ_id}/test")
    def integration_test(integ_id: int) -> dict:
        integ = store.get_integration(integ_id, with_secret=True)
        if not integ:
            raise HTTPException(404, "no such integration")
        url = (integ.get("base_url") or "").rstrip("/")
        if not url:
            return {"ok": False, "error": "no base URL set"}
        headers = {}
        at, sec = integ.get("auth_type"), integ.get("secret") or ""
        cfg = integ.get("config") or {}
        if at == "bearer" and sec:
            headers["Authorization"] = f"Bearer {sec}"
        elif at == "api_key" and sec:
            headers[cfg.get("header_name") or "Authorization"] = sec
        elif at == "basic" and sec:
            headers["Authorization"] = "Basic " + base64.b64encode(
                f"{cfg.get('username', '')}:{sec}".encode()).decode()
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=8) as r:
                return {"ok": True, "status": r.status}
        except Exception as e:
            code = getattr(e, "code", None)
            # a 401/403/404 still proves we reached the host
            return {"ok": bool(code), "status": code, "error": str(e)[:160]}

    # --- NPI cockpit: every project's pipeline readiness at a glance -----------
    _COCKPIT_STAGES = ["identity", "diagram", "pinout", "pcb", "findings", "profile", "product"]

    @app.get("/api/cockpit")
    def cockpit(request: Request) -> list[dict]:
        u = current_user(request)
        acc = None if u["role"] == "admin" else store.access_map(u["id"])
        pt = store.project_team_map()
        orgs_by_id = {o["id"]: o for o in store.list_orgs()}
        out = []
        for v in store.list_vehicles():
            if acc is not None and v["id"] not in acc:
                continue
            st = store.project_stats(v["id"])
            prod = store.match_product(make=v.get("make", ""), model=v.get("model", ""),
                                       year=v.get("year", ""))
            stages = {
                "identity": bool(v.get("make") or v.get("model") or v.get("tags")),
                "diagram": st["diagrams"] > 0,
                "pinout": st["pinouts"] > 0,
                "pcb": st["components"] > 0,
                "findings": st["memories"] > 0 or st["measurements"] > 0,
                "profile": st["has_profile"],
                "product": prod is not None,
            }
            done = sum(1 for k in _COCKPIT_STAGES if stages[k])
            nxt = next((k for k in _COCKPIT_STAGES if not stages[k]), None)
            owner = orgs_by_id.get(pt[v["id"]]["org_id"]) if v["id"] in pt else None
            out.append({
                "id": v["id"], "label": v.get("label", ""), "make": v.get("make", ""),
                "model": v.get("model", ""), "year": v.get("year", ""), "tags": v.get("tags", []),
                "stages": stages, "progress": round(done / len(_COCKPIT_STAGES) * 100),
                "next": nxt, "units": prod["units"] if prod else None,
                "team": _team_brief(owner), "updated_at": v.get("created_at", ""),
            })
        return out

    # --- product library (turn a project into a reusable, listable SKU) --------
    @app.get("/api/products")
    def products_list() -> list[dict]:
        return store.list_products()

    @app.get("/api/product/{product_id}")
    def product_get(product_id: int) -> dict:
        p = store.get_product(product_id)
        if not p:
            raise HTTPException(404, "no such product")
        return productlib.hydrate(p)

    @app.delete("/api/product/{product_id}")
    def product_delete(product_id: int) -> dict:
        store.delete_product(product_id)
        return {"ok": True}

    @app.post("/api/vehicles/{vehicle_id}/promote")
    def promote_to_product(vehicle_id: int) -> dict:
        fields = productlib.build_product_fields(store, vehicle_id)
        return productlib.hydrate(store.upsert_product(**fields))

    @app.get("/api/vehicles/{vehicle_id}/product-match")
    def product_match(vehicle_id: int) -> dict:
        v = store.get_vehicle(vehicle_id)
        prof = store.get_profile(vehicle_id) or ""
        pn = ""
        if prof:
            try:
                pn = ModuleProfile.from_yaml(prof).identity.part_number
            except Exception:
                pass
        m = store.match_product(sku=pn, make=v.get("make", ""), model=v.get("model", ""),
                                year=v.get("year", ""))
        # don't match a project to the product it created
        if m and m.get("source_vehicle_id") == vehicle_id:
            m = None
        return {"match": productlib.hydrate(m) if m else None}

    @app.post("/api/product/{product_id}/listing")
    def product_listing(product_id: int) -> dict:
        p = store.get_product(product_id)
        if not p:
            raise HTTPException(404, "no such product")
        ph = productlib.hydrate(p)
        identity = " ".join(filter(None, [ph.get("year"), ph.get("make"), ph.get("model"),
                            ph.get("module_class"), f"(P/N {ph['part_number']})"
                            if ph.get("part_number") else ""]))
        symptoms = "\n".join(f"- {s}" for s in (ph.get("symptoms") or []))
        scope = "\n".join(f"- {b.get('ref')} {b.get('part', '')}".strip()
                          for b in (ph.get("bom") or []))
        try:
            md = extract.product_listing(client, identity=identity, symptoms=symptoms, scope=scope)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        return {"listing": md}

    # --- module profile (CAB contract: diagram/PCB -> confirmed profile) -------
    def _profile_payload(yaml_text: str, saved: bool) -> dict:
        try:
            prof = ModuleProfile.from_yaml(yaml_text).model_dump()
        except Exception:
            prof = None
        return {"yaml": yaml_text, "saved": saved, "profile": prof}

    @app.get("/api/vehicles/{vehicle_id}/profile")
    def get_profile(vehicle_id: int) -> dict:
        saved = store.get_profile(vehicle_id)
        if saved:
            return _profile_payload(saved, True)
        return _profile_payload(profile_generate.build_profile(store, vehicle_id).to_yaml(), False)

    @app.post("/api/vehicles/{vehicle_id}/profile/generate")
    def regenerate_profile(vehicle_id: int) -> dict:
        return _profile_payload(profile_generate.build_profile(store, vehicle_id).to_yaml(), False)

    @app.put("/api/vehicles/{vehicle_id}/profile")
    def save_profile(vehicle_id: int, body: ProfileBody) -> dict:
        try:
            ModuleProfile.from_yaml(body.yaml)  # validate before persisting
        except Exception as e:
            raise HTTPException(400, f"invalid profile: {e}") from e
        store.save_profile(vehicle_id, body.yaml)
        return {"ok": True, "saved": True}

    # --- recorded measurements (DMM/scope -> project, for audit + wiki) --------
    @app.get("/api/vehicles/{vehicle_id}/measurements")
    def list_measurements(vehicle_id: int) -> list[dict]:
        return store.list_measurements(vehicle_id)

    @app.post("/api/vehicles/{vehicle_id}/measurement")
    def add_measurement(vehicle_id: int, body: MeasurementBody) -> dict:
        attachment_id = None
        if body.image:  # a scope capture PNG -> save as an attachment so the wiki can embed it
            try:
                raw = base64.b64decode(_decode_b64_image(body.image))
                path = config.uploads_dir / f"v{vehicle_id}_meas_{int(time.time() * 1000)}.png"
                path.write_bytes(raw)
                att = store.add_attachment(
                    vehicle_id, str(path), kind="measurement", note=body.label[:200])
                attachment_id = att["id"]
            except (ValueError, OSError):
                pass
        data = json.dumps(body.data) if body.data is not None else None
        return store.add_measurement(
            vehicle_id, kind=body.kind, label=body.label, mode=body.mode, value=body.value,
            unit=body.unit, data=data, attachment_id=attachment_id, note=body.note)

    @app.delete("/api/measurement/{measurement_id}")
    def delete_measurement(measurement_id: int) -> dict:
        store.delete_measurement(measurement_id)
        return {"ok": True}

    # --- guided walkthrough (physics-first, step-by-step) ----------------------
    @app.get("/api/vehicles/{vehicle_id}/guided/log")
    def guided_log(vehicle_id: int) -> list[dict]:
        return store.list_messages(vehicle_id, channel="guided")

    @app.post("/api/vehicles/{vehicle_id}/guided/next")
    def guided_next(vehicle_id: int, body: GuidedNextBody) -> dict:
        log_msgs = store.list_messages(vehicle_id, channel="guided")
        log = "\n".join(m["content"] for m in log_msgs)
        context = kb.context_block(f"{body.symptom} {body.phase}") + "\n\n" \
            + chat_context(vehicle_id, body.symptom or body.phase)
        try:
            return extract.guided_next(
                client, context=context, phase=body.phase, symptom=body.symptom, log=log)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e

    @app.post("/api/vehicles/{vehicle_id}/guided/next/stream")
    def guided_next_stream(vehicle_id: int, body: GuidedNextBody) -> StreamingResponse:
        log_msgs = store.list_messages(vehicle_id, channel="guided")
        log = "\n".join(m["content"] for m in log_msgs)
        context = kb.context_block(f"{body.symptom} {body.phase}") + "\n\n" \
            + chat_context(vehicle_id, body.symptom or body.phase)

        def gen():
            try:
                for kind, payload in extract.guided_next_stream(
                    client, context=context, phase=body.phase, symptom=body.symptom, log=log):
                    if kind == "think":
                        yield f"event: token\ndata: {json.dumps(payload)}\n\n"
                    else:  # final structured step
                        yield f"event: done\ndata: {json.dumps(payload)}\n\n"
            except OllamaError as e:
                yield f"event: error\ndata: {json.dumps(str(e))}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/api/vehicles/{vehicle_id}/guided/step")
    def guided_step(vehicle_id: int, body: GuidedStepBody) -> dict:
        entry = f"[{body.phase}] {body.title} → {body.status.upper()}"
        if body.result:
            entry += f": {body.result}"
        store.add_message(vehicle_id, "user", entry, channel="guided")
        # A confirmed finding compounds into the cross-module case history.
        if body.status in ("fail", "finding"):
            save_memory_if_novel(vehicle_id, f"Guided finding — {entry}", "case")
        return {"ok": True}

    @app.post("/api/vehicles/{vehicle_id}/report")
    def repair_report(vehicle_id: int) -> dict:
        v = store.get_vehicle(vehicle_id)
        msgs = store.list_messages(vehicle_id, channel="triage")
        transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in msgs)
        facts = (
            f"Module: {' '.join(filter(None, [v['year'], v['make'], v['model'], v['label']]))}\n"
            f"VIN: {v['vin'] or '(unknown)'}\nTags: {', '.join(store.list_tags(vehicle_id))}\n"
            f"Pinout:\n{_pinout_text(store.list_pinouts(vehicle_id))}"
        )
        if not transcript.strip():
            return {"report": "_No triage conversation yet — start a triage session first._"}
        try:
            return {"report": extract.repair_report(client, transcript, facts)}
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e

    # --- attachments (board/scope/phone photos) --------------------------------
    @app.get("/api/vehicles/{vehicle_id}/attachments")
    def list_attachments(vehicle_id: int) -> list[dict]:
        return store.list_attachments(vehicle_id)

    @app.post("/api/vehicles/{vehicle_id}/annotation")
    def save_annotation(vehicle_id: int, body: AnnotationBody) -> dict:
        b64 = _decode_b64_image(body.image)
        try:
            raw = base64.b64decode(b64)
            path = config.uploads_dir / f"v{vehicle_id}_anno_{int(time.time() * 1000)}.png"
            path.write_bytes(raw)
        except (ValueError, OSError) as e:
            raise HTTPException(400, "bad image") from e
        att = store.add_attachment(
            vehicle_id, str(path), kind="annotation", note=body.note[:300])
        return {"id": att["id"], "kind": att["kind"], "note": att["note"] or ""}

    @app.get("/api/attachment/{attachment_id}/image")
    def attachment_image(attachment_id: int, request: Request) -> Response:
        row = store.get_attachment(attachment_id)
        if not row or not Path(row["path"]).exists():
            raise HTTPException(404, "not found")
        p = Path(row["path"])
        st = p.stat()
        # attachment files are written once -> safe to cache hard with a revalidation ETag
        etag = f'"{attachment_id}-{int(st.st_mtime)}-{st.st_size}"'
        cache = {"Cache-Control": "private, max-age=604800", "ETag": etag}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=cache)
        ext = p.suffix.lower()
        mt = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        return Response(content=p.read_bytes(), media_type=mt, headers=cache)

    @app.get("/api/attachment/{attachment_id}")
    def attachment_meta(attachment_id: int) -> dict:
        row = store.get_attachment(attachment_id)
        if not row:
            raise HTTPException(404, "not found")
        return {"id": row["id"], "kind": row["kind"], "note": row["note"] or ""}

    @app.patch("/api/attachment/{attachment_id}")
    def attachment_update(attachment_id: int, body: AttachmentUpdate) -> dict:
        row = store.update_attachment(attachment_id, note=body.note)
        if not row:
            raise HTTPException(404, "not found")
        return {"id": row["id"], "kind": row["kind"], "note": row["note"] or ""}

    @app.delete("/api/attachment/{attachment_id}")
    def attachment_delete(attachment_id: int) -> dict:
        row = store.get_attachment(attachment_id)
        if not row:
            raise HTTPException(404, "not found")
        store.delete_attachment(attachment_id)
        try:
            Path(row["path"]).unlink(missing_ok=True)  # best-effort file cleanup
        except OSError:
            pass
        return {"ok": True}

    # --- phone pairing (snap board photos straight into a project) -------------
    @app.get("/api/vehicles/{vehicle_id}/pair")
    def pair(vehicle_id: int, request: Request) -> dict:
        token = auth.make_pair_token(secret, vehicle_id)
        base = str(request.base_url).rstrip("/")
        return {"token": token, "url": f"{base}/m?token={token}"}

    @app.get("/api/vehicles/{vehicle_id}/pair/qr")
    def pair_qr(vehicle_id: int, request: Request) -> Response:
        import io

        import qrcode
        token = auth.make_pair_token(secret, vehicle_id)
        url = f"{str(request.base_url).rstrip('/')}/m?token={token}"
        buf = io.BytesIO()
        qrcode.make(url).save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")

    @app.get("/m")
    def mobile_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "mobile.html")

    @app.get("/api/pair/info")
    def pair_info(token: str) -> dict:
        vid = auth.valid_pair_token(secret, token)
        if vid is None:
            raise HTTPException(401, "invalid or expired pairing link")
        v = store.get_vehicle(vid)
        return {"vehicle_id": vid, "label": v["label"] or " ".join(
            filter(None, [v["year"], v["make"], v["model"]])) or f"project {vid}"}

    @app.post("/api/pair/upload")
    async def pair_upload(token: str = Form(...), kind: str = Form("phone"),
                          file: UploadFile = None) -> dict:
        vid = auth.valid_pair_token(secret, token)
        if vid is None:
            raise HTTPException(401, "invalid or expired pairing link")
        if file is None:
            raise HTTPException(400, "no file")
        data = await file.read()
        path = config.uploads_dir / f"v{vid}_phone_{int(time.time() * 1000)}.jpg"
        try:
            path.write_bytes(dg.downscale_photo(data))  # compact JPEG, safety-downscale if large
        except Exception:
            path = path.with_suffix(".png")
            path.write_bytes(data)
        rec = store.add_attachment(vid, str(path), kind=kind, note=file.filename or "phone photo")
        return {"ok": True, "id": rec["id"]}

    # --- deep research ---------------------------------------------------------
    @app.post("/api/research")
    def research(body: ResearchBody) -> dict:
        out = researchmod.search(body.query)
        if body.synthesize and out.get("results"):
            srcs = "\n".join(
                f"[{i + 1}] {r['title']} — {r['url']}\n{r['snippet'][:220]}"
                for i, r in enumerate(out["results"])
            )
            try:
                msgs = [
                    ChatMessage("system", RESEARCH_SYSTEM),
                    ChatMessage("user", f"Question: {body.query}\n\nSOURCES:\n{srcs}"),
                ]
                out["summary"] = client.chat(msgs, temperature=0.2)
            except OllamaError:
                out["summary"] = ""
        return out

    # --- per-project wiki (compiled, shareable) --------------------------------
    @app.get("/api/vehicles/{vehicle_id}/wiki")
    def project_wiki(vehicle_id: int) -> dict:
        return {"markdown": wikimod.build(store, vehicle_id)}

    # --- house knowledge base (curated troubleshooting best-practices) ---------
    @app.get("/api/knowledge")
    def knowledge_list(response: Response) -> list[dict]:
        response.headers["Cache-Control"] = "private, max-age=600"  # KB is static within a run
        return [{"slug": a.slug, "title": a.title, "tags": a.tags} for a in kb.load_articles()]

    @app.get("/api/knowledge/{slug}")
    def knowledge_article(slug: str, response: Response) -> dict:
        a = next((a for a in kb.load_articles() if a.slug == slug), None)
        if a is None:
            raise HTTPException(404, "no such article")
        response.headers["Cache-Control"] = "private, max-age=600"
        return {"slug": a.slug, "title": a.title, "tags": a.tags, "body": a.body}

    # --- bench instruments (DMM / scope / signal generator) --------------------
    instruments = InstrumentHub()

    @app.get("/api/instr/status")
    def instr_status() -> dict:
        return instruments.status()

    @app.post("/api/instr/connect")
    def instr_connect(body: InstrConnectBody) -> dict:
        return instruments.connect(body.source or body.port or None)

    @app.get("/api/instr/ports")
    def instr_ports() -> dict:
        ports = []
        try:
            from serial.tools import list_ports
            ports = [{"device": p.device, "desc": p.description or ""}
                     for p in list_ports.comports()]
        except Exception:
            pass
        return {"ports": ports}

    @app.get("/api/instr/visa")
    def instr_visa() -> dict:
        from canopy.hal.visa import list_resources
        return list_resources()

    @app.get("/api/instr/dmm")
    def instr_dmm(mode: str = "vdc") -> dict:
        return instruments.dmm(mode)

    @app.get("/api/instr/siggen")
    def instr_siggen_get() -> dict:
        return instruments.get_siggen()

    @app.post("/api/instr/siggen")
    def instr_siggen_set(body: SigGenBody) -> dict:
        return instruments.set_siggen(**body.model_dump(exclude_none=True))

    @app.get("/api/instr/scope/stream")
    def instr_scope_stream(timebase: float = 0.001, samples: int = 480, trig_level: float = 0.0,
                           trig_edge: str = "rising", coupling: str = "dc") -> StreamingResponse:
        samples = max(64, min(2000, samples))

        def gen():
            frame = 0
            while True:
                frame += 1
                fr = instruments.scope_frame(
                    timebase, samples, frame, trig_level, trig_edge, coupling)
                yield f"data: {json.dumps(fr)}\n\n"
                time.sleep(0.04)  # ~25 fps

        return StreamingResponse(gen(), media_type="text/event-stream")

    # --- USB-to-CAN bench ------------------------------------------------------
    bench = benchmod.BenchManager()

    @app.get("/api/can/interfaces")
    def can_interfaces() -> list[dict]:
        return benchmod.list_can_interfaces()

    @app.get("/api/can/status")
    def can_status() -> dict:
        return bench.status()

    @app.post("/api/can/connect")
    def can_connect(body: ConnectBody) -> dict:
        try:
            return bench.connect(body.interface, body.channel, body.bitrate, body.fd)
        except Exception as e:
            raise HTTPException(400, f"connect failed: {e}") from e

    @app.post("/api/can/disconnect")
    def can_disconnect() -> dict:
        return bench.disconnect()

    @app.get("/api/can/frames")
    def can_frames(since: int = 0) -> dict:
        return {"frames": bench.recent_frames(since), "status": bench.status()}

    @app.post("/api/can/send")
    def can_send(body: SendFrameBody) -> dict:
        try:
            data = bytes.fromhex(body.data.replace(" ", "")) if body.data else b""
            return bench.send_frame(_parse_id(body.id), data, extended=body.extended)
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/api/can/ping")
    def can_ping(body: PingBody) -> dict:
        try:
            return bench.ping_ecu(_parse_id(body.request_id), _parse_id(body.response_id))
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/api/can/uds")
    def can_uds(body: UdsBody) -> dict:
        try:
            payload = bytes.fromhex(body.payload.replace(" ", ""))
            if not payload:
                raise ValueError("empty UDS payload")
            req, rsp = _parse_id(body.request_id), _parse_id(body.response_id)
            return bench.uds_request(req, rsp, payload)
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/api/can/dtcs")
    def can_dtcs(body: PingBody) -> dict:
        try:
            return bench.read_dtcs(_parse_id(body.request_id), _parse_id(body.response_id))
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    # --- restbus (DBC-driven vehicle emulation) --------------------------------
    @app.post("/api/can/dbc")
    async def can_dbc_upload(file: UploadFile) -> dict:
        data = await file.read()
        path = config.uploads_dir / f"dbc_{int(time.time())}_{file.filename or 'platform.dbc'}"
        path.write_bytes(data)
        try:
            summary = bench.restbus.load_dbc(str(path))
            bench.restbus.dbc_name = file.filename or bench.restbus.dbc_name
            summary["dbc"] = bench.restbus.dbc_name
            return summary
        except Exception as e:
            raise HTTPException(400, f"could not load DBC: {e}") from e

    @app.get("/api/can/restbus")
    def can_restbus_status() -> dict:
        return bench.restbus.summary()

    @app.post("/api/can/restbus/start")
    def can_restbus_start(body: RestbusBody) -> dict:
        try:
            return bench.restbus_start(body.messages or None)
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/api/can/restbus/stop")
    def can_restbus_stop() -> dict:
        return bench.restbus_stop()

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(OllamaError)
    def _ollama_error(_request, exc: OllamaError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    return app
