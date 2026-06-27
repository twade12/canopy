"""SQLAlchemy models mirroring the data model in CLAUDE.md §6.

Diagnosis loop: a new run's ``SymptomVector`` is matched (nearest-neighbor) against
historical ``Case`` rows → ranked likely root causes; the labeled cases are also the wiki.
Portable types now (JSON embedding); Phase 1 swaps Postgres/Timescale/pgvector in.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Module(Base):
    """A module type under test (make/model/part)."""

    __tablename__ = "module"

    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    part_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    profile_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    adapters: Mapped[list[Adapter]] = relationship(back_populates="module")
    runs: Mapped[list[TestRun]] = relationship(back_populates="module")


class Adapter(Base):
    """A per-module adapter harness mapping its connector to the standard test header."""

    __tablename__ = "adapter"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id"))
    harness_id: Mapped[str] = mapped_column(String(64))   # physical harness identity (EEPROM/QR)
    header_pin_map: Mapped[dict] = mapped_column(JSON, default=dict)

    module: Mapped[Module] = relationship(back_populates="adapters")


class TestRun(Base):
    """One execution of a profile against a module."""

    __tablename__ = "test_run"
    __test__ = False  # not a pytest test class

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    profile_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_trace_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[str | None] = mapped_column(String(16), nullable=True)   # pass / fail / error

    module: Mapped[Module] = relationship(back_populates="runs")
    observations: Mapped[list[Observation]] = relationship(back_populates="run")
    symptom_vector: Mapped[SymptomVector | None] = relationship(back_populates="run", uselist=False)
    case: Mapped[Case | None] = relationship(back_populates="run", uselist=False)


class Observation(Base):
    """A single measured fact from a run (missing CAN id, DTC, current draw, rail V, …)."""

    __tablename__ = "observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_run.id"))
    type: Mapped[str] = mapped_column(String(48))
    value: Mapped[dict] = mapped_column(JSON, default=dict)

    run: Mapped[TestRun] = relationship(back_populates="observations")


class SymptomVector(Base):
    """Feature/symptom embedding of a run's observations (pgvector in Phase 1)."""

    __tablename__ = "symptom_vector"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_run.id"))
    embedding: Mapped[list] = mapped_column(JSON, default=list)

    run: Mapped[TestRun] = relationship(back_populates="symptom_vector")


class Case(Base):
    """A labeled, component-level root cause — diagnosis training data *and* wiki content."""

    __tablename__ = "case"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("test_run.id"))
    root_cause: Mapped[str] = mapped_column(Text)            # e.g. "U3 5V LDO open"
    component_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    repair_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    technician: Mapped[str | None] = mapped_column(String(64), nullable=True)

    run: Mapped[TestRun] = relationship(back_populates="case")
