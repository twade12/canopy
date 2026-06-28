"""FastAPI app: local wiring-diagram vision + chat server.

Serves an attractive single-page UI and a small JSON API. All inference runs against a
local Ollama model; all data (diagrams, VINs, memories) stays on this machine.
"""

from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from canopy.vision import auth, extract
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
    password: str = ""
    secure: bool = False


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
    secret = auth.load_secret(config.data_dir)

    @app.middleware("http")
    async def require_auth(request, call_next):
        if not config.password:
            return await call_next(request)
        path = request.url.path
        # /m (mobile capture) + /api/pair/* are gated by a pairing token, not the password.
        if (path in ("/login", "/api/login", "/healthz", "/m", "/favicon.ico")
                or path.startswith("/static") or path.startswith("/api/pair/")):
            return await call_next(request)
        if auth.valid_token(secret, request.cookies.get(auth.COOKIE)):
            return await call_next(request)
        if path.startswith("/api"):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        return RedirectResponse("/login")

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
        if not config.password or auth.check_password(config.password, body.password):
            resp = JSONResponse({"ok": True})
            resp.set_cookie(auth.COOKIE, auth.make_token(secret), httponly=True,
                            samesite="lax", max_age=auth.TTL, secure=body.secure)
            return resp
        return JSONResponse(status_code=401, content={"detail": "wrong password"})

    @app.post("/api/logout")
    def logout() -> JSONResponse:
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(auth.COOKIE)
        return resp

    @app.get("/api/auth/status")
    def auth_status() -> dict:
        return {"auth": bool(config.password)}

    store = make_store(config)
    client = OllamaClient(
        config.ollama_url, config.model, timeout=config.request_timeout
    )
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
    def list_vehicles() -> list[dict]:
        return store.list_vehicles()

    @app.post("/api/vehicles")
    def create_vehicle(body: VehicleBody) -> dict:
        return store.create_vehicle(**body.model_dump())

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
    def attachment_image(attachment_id: int) -> Response:
        row = store.get_attachment(attachment_id)
        if not row or not Path(row["path"]).exists():
            raise HTTPException(404, "not found")
        ext = Path(row["path"]).suffix.lower()
        mt = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        return Response(content=Path(row["path"]).read_bytes(), media_type=mt)

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
    def knowledge_list() -> list[dict]:
        return [{"slug": a.slug, "title": a.title, "tags": a.tags} for a in kb.load_articles()]

    @app.get("/api/knowledge/{slug}")
    def knowledge_article(slug: str) -> dict:
        a = next((a for a in kb.load_articles() if a.slug == slug), None)
        if a is None:
            raise HTTPException(404, "no such article")
        return {"slug": a.slug, "title": a.title, "tags": a.tags, "body": a.body}

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

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(OllamaError)
    def _ollama_error(_request, exc: OllamaError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    return app
