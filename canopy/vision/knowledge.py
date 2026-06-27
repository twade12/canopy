"""CANOPY house knowledge base — curated electronics-triage best practices.

These markdown articles (in ``knowledge/``) are the seed of the team's competitive moat: the
distilled methodology for tracing power / communication / sensor lines and component-level checks
down to a root cause on an *unknown* board. They are injected into every triage / assistant /
PCB-analysis prompt so the AI always reasons like a seasoned repair engineer, and they grow over
time alongside the per-project ``Case`` records that accumulate from real repairs.

Retrieval is keyword-scored (no embedding round-trip needed), which is plenty for a curated set
of a few dozen articles and keeps triage latency low.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
_WORD = re.compile(r"[a-z0-9]+")


@dataclass
class Article:
    slug: str
    title: str
    tags: list[str]
    body: str

    @property
    def terms(self) -> set[str]:
        blob = f"{self.title} {' '.join(self.tags)} {self.body}".lower()
        return set(_WORD.findall(blob))


def _parse(path: Path) -> Article:
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("-", " ").title()
    tags: list[str] = []
    body_lines: list[str] = []
    for ln in text.splitlines():
        if ln.startswith("# ") and title == path.stem.replace("-", " ").title():
            title = ln[2:].strip()
        elif ln.lower().startswith("> tags:"):
            tags = [t.strip() for t in ln.split(":", 1)[1].split(",") if t.strip()]
        else:
            body_lines.append(ln)
    return Article(path.stem, title, tags, "\n".join(body_lines).strip())


@lru_cache(maxsize=1)
def load_articles() -> tuple[Article, ...]:
    if not KNOWLEDGE_DIR.exists():
        return ()
    return tuple(_parse(p) for p in sorted(KNOWLEDGE_DIR.glob("*.md")))


def relevant(query: str, k: int = 3) -> list[Article]:
    """Top-k articles by keyword overlap with the query (tags weighted heavier)."""
    arts = load_articles()
    if not arts:
        return []
    q = set(_WORD.findall((query or "").lower()))
    if not q:
        return list(arts[:k])
    scored = []
    for a in arts:
        tagset = {t for tag in a.tags for t in _WORD.findall(tag.lower())}
        score = len(q & a.terms) + 2 * len(q & tagset)
        scored.append((score, a))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [a for score, a in scored if score > 0][:k] or list(arts[:k])


def core_methodology() -> str:
    """The master methodology article body — always injected, lightly trimmed."""
    for a in load_articles():
        if a.slug == "methodology":
            return a.body
    return ""


# Compact always-on doctrine (kept short so retrieved articles get most of the budget).
CORE_RULES = (
    "CANOPY METHOD: state the symptom as an observable fact; reason ONLY from the real pinout and "
    "what you can measure — never invent voltages, part numbers, or physics. Inspect first, then "
    "bring power up GROUND -> permanent 12V (current-limited) -> ignition -> reference rails, "
    "watching inrush/quiescent current (high = short, near-zero = open). Divide and conquer by "
    "functional block (power -> MCU+clock/reset -> comms -> inputs -> outputs); confirm a block's "
    "precondition before blaming the next. Confirm a fault with a second independent measurement "
    "before replacing anything; repair, then re-verify against the original symptom. A bad ground "
    "mimics almost any fault. For safety/emissions/security systems, recommend authorized "
    "procedures, not bypasses."
)


def context_block(query: str, k: int = 3, max_chars: int = 6500) -> str:
    """A CANOPY-knowledge block to prepend to a triage/assistant prompt: the compact house
    doctrine plus the most relevant full articles from the knowledge base for this symptom."""
    parts = ["CANOPY FIELD KNOWLEDGE — apply these house best-practices; cite the actual pinout, "
             "never invent values.", CORE_RULES]
    for a in relevant(query, k):
        parts.append(f"--- {a.title} ---\n{a.body}")
    return "\n\n".join(parts)[:max_chars]
