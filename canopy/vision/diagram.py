"""Diagram file handling: accept image or PDF, render to base64 PNG for the model.

The multimodal model ingests images. PDFs are rendered page-by-page with PyMuPDF. Large
images are downscaled so the model isn't overwhelmed and inference stays responsive.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

MAX_DIM = 2000  # px; downscale longer edge to keep payloads/inference reasonable


def is_pdf(filename: str, mime: str) -> bool:
    return mime == "application/pdf" or filename.lower().endswith(".pdf")


def save_upload(uploads_dir: Path, vehicle_id: int, filename: str, data: bytes) -> Path:
    """Persist an uploaded diagram, namespaced by vehicle, returning its path."""
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe = Path(filename).name or "diagram"
    dest = uploads_dir / f"v{vehicle_id}_{safe}"
    dest.write_bytes(data)
    return dest


def _downscale_png(data: bytes) -> bytes:
    """Return PNG bytes, downscaled if larger than MAX_DIM on the longer edge."""
    from PIL import Image

    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    if max(img.size) > MAX_DIM:
        scale = MAX_DIM / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def render_pdf_pages(path: Path, *, max_pages: int = 4, zoom: float = 2.0) -> list[bytes]:
    """Render up to `max_pages` PDF pages to PNG bytes at `zoom` scale."""
    import fitz  # PyMuPDF

    images: list[bytes] = []
    with fitz.open(str(path)) as doc:
        for page in doc[:max_pages]:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            images.append(_downscale_png(pix.tobytes("png")))
    return images


def to_png_images(path: Path, mime: str) -> list[bytes]:
    """Normalize any uploaded diagram to a list of PNG byte buffers."""
    if is_pdf(path.name, mime):
        return render_pdf_pages(path)
    return [_downscale_png(path.read_bytes())]


def page_count(path: Path, mime: str) -> int:
    if is_pdf(path.name, mime):
        import fitz

        with fitz.open(str(path)) as doc:
            return doc.page_count
    return 1


def b64(images: list[bytes]) -> list[str]:
    """Base64-encode PNG buffers for the Ollama image field."""
    return [base64.b64encode(buf).decode("ascii") for buf in images]
