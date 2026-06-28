"""Diagram file handling: per-page render + embedded-text extraction.

Multi-page service PDFs (e.g. a 24-page Ford wiring diagram) carry a reliable *text layer*
with pin numbers, signal labels, circuit IDs, and colors. We feed that text to the model
*alongside* the rendered page image — far more accurate than vision alone — and we work one
page at a time, since each page is usually one connector view.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

MAX_DIM = 2200  # px; downscale longer edge to keep payloads/inference reasonable
PAGE_ZOOM = 2.4  # render scale for PDF pages (legibility of small pin labels)


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

    img = Image.open(io.BytesIO(data)).convert("RGB")
    if max(img.size) > MAX_DIM:
        scale = MAX_DIM / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def downscale_photo(data: bytes, max_dim: int = 1600, quality: int = 85) -> bytes:
    """Downscale a photograph and return compact JPEG bytes (photos compress far better as
    JPEG than PNG — keeps phone uploads small and fast to serve back to the desktop)."""
    from PIL import Image

    img = Image.open(io.BytesIO(data)).convert("RGB")
    if max(img.size) > max_dim:
        scale = max_dim / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def page_count(path: Path, mime: str) -> int:
    if is_pdf(path.name, mime):
        import fitz

        with fitz.open(str(path)) as doc:
            return doc.page_count
    return 1


def render_page(path: Path, mime: str, index: int = 0) -> bytes:
    """Render a single page (PDF) or the image itself to downscaled PNG bytes."""
    if is_pdf(path.name, mime):
        import fitz

        with fitz.open(str(path)) as doc:
            index = max(0, min(index, doc.page_count - 1))
            pix = doc[index].get_pixmap(matrix=fitz.Matrix(PAGE_ZOOM, PAGE_ZOOM))
            return _downscale_png(pix.tobytes("png"))
    return _downscale_png(path.read_bytes())


ROW_TOL = 3.2  # points; words within this Y distance share a visual row
COL_GAP = 12.0  # points; a larger X gap is treated as a column break


def _layout_text(words: list[tuple]) -> str:
    """Reconstruct row/column-aligned text from positioned words.

    PyMuPDF ``get_text("words")`` returns ``(x0, y0, x1, y1, word, block, line, n)``.
    The default linear ``get_text()`` follows the PDF content-stream order, which on
    schematic-style diagrams (e.g. GM/ALLDATA) scrambles a connector's pin numbers,
    signal names, colors, and circuits into three separate clumps — actively misleading
    the model. Grouping words by Y into rows and ordering by X keeps each pin's
    ``number  signal  color  circuit`` together on one line, so the model can read across.
    """
    if not words:
        return ""
    rows: list[list[tuple]] = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        if rows and abs(w[1] - rows[-1][0][1]) <= ROW_TOL:
            rows[-1].append(w)
        else:
            rows.append([w])
    lines = []
    for row in rows:
        row.sort(key=lambda w: w[0])
        s, prev_x1 = "", None
        for w in row:
            if prev_x1 is not None:
                s += "    " if (w[0] - prev_x1) > COL_GAP else " "
            s += w[4]
            prev_x1 = w[2]
        lines.append(s)
    return "\n".join(lines)


def page_text(path: Path, mime: str, index: int = 0) -> str:
    """Return a layout-reconstructed text layer for a PDF page ('' for images)."""
    if not is_pdf(path.name, mime):
        return ""
    import fitz

    with fitz.open(str(path)) as doc:
        index = max(0, min(index, doc.page_count - 1))
        page = doc[index]
        return _layout_text(page.get_text("words")) or page.get_text().strip()


def b64(images: list[bytes]) -> list[str]:
    """Base64-encode PNG buffers for the Ollama image field."""
    return [base64.b64encode(buf).decode("ascii") for buf in images]


def b64_page(path: Path, mime: str, index: int = 0) -> list[str]:
    """Convenience: render one page and return it as a single-element base64 list."""
    return b64([render_page(path, mime, index)])
