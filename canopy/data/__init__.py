"""Persistence layer — the part that compounds (CLAUDE.md §6).

Every run writes a structured record; labeled `Case` rows are simultaneously the diagnosis
training data and the wiki content. Models are kept portable (generic SQLAlchemy types) so
they create on SQLite in tests today and migrate to Postgres + Timescale + pgvector in
Phase 1. The embedding column moves from JSON to a real ``vector`` type then.
"""

from canopy.data.models import (
    Adapter,
    Base,
    Case,
    Module,
    Observation,
    SymptomVector,
    TestRun,
)

__all__ = ["Base", "Module", "Adapter", "TestRun", "Observation", "SymptomVector", "Case"]
