"""Configuration for the local vision/chat server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class VisionConfig:
    """Settings, all overridable by ``CANOPY_*`` env vars.

    Attributes:
        ollama_url: Base URL of the local Ollama server.
        model: Multimodal model name (must accept image input). Default: the user's
            ``gemma4:26b``; ``gemma3:27b`` / ``gemma3:12b`` are good fallbacks.
        data_dir: Where the SQLite DB and uploaded diagrams live.
        request_timeout: Seconds to wait on an Ollama generation (models are large/slow).
    """

    ollama_url: str = "http://localhost:11434"
    model: str = "gemma4:26b"
    embed_model: str = "nomic-embed-text"
    data_dir: Path = Path.home() / ".canopy" / "vision"
    request_timeout: float = 600.0
    password: str = ""  # CANOPY_PASSWORD; empty disables auth (local/dev)
    database_url: str = ""  # CANOPY_DATABASE_URL; empty = local SQLite, else Postgres+pgvector

    @classmethod
    def from_env(cls, **overrides) -> VisionConfig:
        d = cls()  # slots=True: read defaults from an instance, not the class descriptors
        cfg = cls(
            ollama_url=os.environ.get("CANOPY_OLLAMA_URL", d.ollama_url),
            model=os.environ.get("CANOPY_OLLAMA_MODEL", d.model),
            embed_model=os.environ.get("CANOPY_OLLAMA_EMBED_MODEL", d.embed_model),
            data_dir=Path(os.environ.get("CANOPY_VISION_DATA", str(d.data_dir))),
            request_timeout=float(os.environ.get("CANOPY_OLLAMA_TIMEOUT", d.request_timeout)),
            password=os.environ.get("CANOPY_PASSWORD", d.password),
            database_url=os.environ.get("CANOPY_DATABASE_URL", d.database_url),
        )
        for key, value in overrides.items():
            if value is not None:
                setattr(cfg, key, value)
        return cfg

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "canopy_vision.db"

    def ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
