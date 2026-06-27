"""FastAPI app: local wiring-diagram vision + chat server.

Serves an attractive single-page UI and a small JSON API. All inference runs against a
local Ollama model; all data (diagrams, VINs, memories) stays on this machine.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from canopy.vision import diagram as dg
from canopy.vision import extract
from canopy.vision.config import VisionConfig
from canopy.vision.ollama_client import ChatMessage, OllamaClient, OllamaError
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


def _pinout_text(pinouts: list[dict]) -> str:
    if not pinouts:
        return "(no pinout extracted yet)"
    lines = ["connector | pin | signal | wire_color | mating"]
    for p in pinouts:
        lines.append(
            f"{p['connector']} | {p['pin']} | {p['signal']} | {p['wire_color']} | {p['mating']}"
        )
    return "\n".join(lines)


def _vehicle_context(store: Store, vehicle_id: int) -> str:
    v = store.get_vehicle(vehicle_id)
    ident = " ".join(filter(None, [v["year"], v["make"], v["model"]])) or "(unidentified)"
    mems = [m["content"] for m in store.list_memories(vehicle_id)]
    parts = [
        f"VEHICLE: {ident}  VIN: {v['vin'] or '(unknown)'}",
        "SAVED MEMORIES:\n" + ("\n".join(f"- {m}" for m in mems) if mems else "- (none)"),
        "EXTRACTED PINOUT:\n" + _pinout_text(store.list_pinouts(vehicle_id)),
    ]
    return "\n\n".join(parts)


def create_app(config: VisionConfig | None = None) -> FastAPI:
    config = config or VisionConfig.from_env()
    config.ensure_dirs()

    app = FastAPI(title="CANOPY Vision", docs_url="/api/docs")
    store = Store(config.db_path)
    client = OllamaClient(
        config.ollama_url, config.model, timeout=config.request_timeout
    )
    image_cache: dict[int, list[str]] = {}

    def images_for_vehicle(vehicle_id: int) -> list[str]:
        d = store.latest_diagram(vehicle_id)
        if d is None:
            return []
        if d["id"] not in image_cache:
            pngs = dg.to_png_images(Path(d["path"]), d["mime"])
            image_cache[d["id"]] = dg.b64(pngs)
        return image_cache[d["id"]]

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
    def diagram_image(diagram_id: int) -> Response:
        try:
            d = store.get_diagram(diagram_id)
        except KeyError:
            raise HTTPException(404, "diagram not found") from None
        pngs = dg.to_png_images(Path(d["path"]), d["mime"])
        return Response(content=pngs[0], media_type="image/png")

    # --- AI actions ------------------------------------------------------------
    def _require_images(vehicle_id: int) -> list[str]:
        imgs = images_for_vehicle(vehicle_id)
        if not imgs:
            raise HTTPException(400, "upload a diagram first")
        return imgs

    @app.post("/api/vehicles/{vehicle_id}/extract")
    def extract_pinout(vehicle_id: int) -> dict:
        imgs = _require_images(vehicle_id)
        d = store.latest_diagram(vehicle_id)
        try:
            result = extract.extract_pinout(client, imgs)
        except OllamaError as e:
            raise HTTPException(503, str(e)) from e
        pinouts = store.replace_pinouts(vehicle_id, d["id"] if d else None, result["pins"])
        return {"connector": result["connector"], "pinouts": pinouts}

    @app.post("/api/vehicles/{vehicle_id}/identify")
    def identify_vehicle(vehicle_id: int) -> dict:
        imgs = _require_images(vehicle_id)
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
    def can_plan(vehicle_id: int) -> dict:
        imgs = _require_images(vehicle_id)
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
        return store.add_memory(vehicle_id, body.content, kind=body.kind)

    @app.delete("/api/memories/{memory_id}")
    def delete_memory(memory_id: int) -> dict:
        store.delete_memory(memory_id)
        return {"ok": True}

    # --- chat ------------------------------------------------------------------
    @app.post("/api/vehicles/{vehicle_id}/chat")
    def chat(vehicle_id: int, body: ChatBody) -> dict:
        imgs = images_for_vehicle(vehicle_id)
        context = _vehicle_context(store, vehicle_id)
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

        suggested: list[str] = []
        if body.save_memories:
            transcript = f"Q: {body.message}\nA: {reply}"
            try:
                suggested = extract.suggest_memories(client, transcript)
            except OllamaError:
                suggested = []
            for fact in suggested:
                store.add_memory(vehicle_id, fact, kind="learned")
        return {"reply": reply, "saved_memories": suggested}

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(OllamaError)
    def _ollama_error(_request, exc: OllamaError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    return app
