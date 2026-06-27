"""Engine/session helpers.

Reads ``CANOPY_DATABASE_URL`` (defaults to the docker-compose Postgres). Tests pass an
explicit SQLite URL. No connection is opened at import time.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from canopy.data.models import Base

DEFAULT_URL = "postgresql+psycopg://canopy:canopy@localhost:5432/canopy"


def make_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    return create_engine(url or os.environ.get("CANOPY_DATABASE_URL", DEFAULT_URL), echo=echo)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_all(engine: Engine) -> None:
    """Create the schema (dev/test convenience; production uses Alembic migrations)."""
    Base.metadata.create_all(engine)
