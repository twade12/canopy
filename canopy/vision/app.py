"""FastAPI app: local wiring-diagram vision + chat server.

Serves an attractive single-page UI and a small JSON API. All inference runs against a
local Ollama model; all data (diagrams, VINs, memories) stays on this machine.
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
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
from canopy.vision import research as researchmod
from canopy.vision.api_reference import API_REFERENCE
from canopy.vision.config import VisionConfig
from canopy.vision.ollama_client import ChatMessage, OllamaClient, OllamaError
from canopy.vision.prompts import RESEARCH_SYSTEM
from canopy.vision.store import Store

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
        if path in ("/login", "/api/login", "/healthz") or path.startswith("/static"):
            return await call_next(request)
        if auth.valid_token(secret, request.cookies.get(auth.COOKIE)):
            return await call_next(request)
        if path.startswith("/api"):
            return JSONResponse(status_code=401, content={"detail": "unauthorized"})
        return RedirectResponse("/login")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

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

    store = Store(config.db_path)
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
        mems = store.list_memories(vehicle_id)
        qvec = embed(question)
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
        mems = store.all_memories()
        qvec = embed(question)
        have = [(m["embedding"], m) for m in mems if m["embedding"]]
        chosen = extract.rank_by_similarity(qvec, have, k=k) if (qvec and have) else mems[:k]
        lines = [f"- [{m['project']}] {m['content']}" for m in chosen]
        projects = store.list_vehicles()
        summary = ", ".join(
            f"{v['label'] or 'project'} ({', '.join(v.get('tags', [])[:4])})" for v in projects[:12]
        )
        return (
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
        """Normalize a possibly-data-URL base64 image to bare base64."""
        return raw.split(",", 1)[1] if raw.startswith("data:") else raw

    @app.get("/api/vehicles/{vehicle_id}/triage/messages")
    def triage_messages(vehicle_id: int) -> list[dict]:
        return store.list_messages(vehicle_id, channel="triage")

    @app.post("/api/vehicles/{vehicle_id}/triage/stream")
    def triage_stream(vehicle_id: int, body: TriageBody) -> StreamingResponse:
        context = chat_context(vehicle_id, body.message)
        history = [
            ChatMessage(m.get("role", "user"), m.get("content", ""))
            for m in body.history if m.get("role") in ("user", "assistant")
        ][-8:]
        images: list[str] = []
        note = body.message
        if body.image:
            b64 = _decode_b64_image(body.image)
            images = [b64]
            try:
                path = config.uploads_dir / f"v{vehicle_id}_triage_{int(time.time() * 1000)}.png"
                path.write_bytes(base64.b64decode(b64))
                store.add_attachment(vehicle_id, str(path), kind="photo", note=body.message[:200])
                note = f"{body.message} [photo attached]"
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
