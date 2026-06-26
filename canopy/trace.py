"""Raw CAN trace logging in Vector-compatible BLF (CLAUDE.md §4, §5).

Every test run writes a raw trace so failures are forensically reproducible. python-can
ships the BLF writer; this wraps it with a per-run path convention and a context manager.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType

import can

DEFAULT_TRACE_DIR = Path("traces")


def default_trace_path(run_id: str | None = None, *, directory: Path | None = None) -> Path:
    """Build a timestamped ``.blf`` path, e.g. ``traces/20260626T184500Z_run.blf``."""
    directory = directory or DEFAULT_TRACE_DIR
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{stamp}_{run_id}.blf" if run_id else f"{stamp}.blf"
    return directory / name


class BlfTraceLogger:
    """Append CAN frames to a BLF file.

    Usage::

        with BlfTraceLogger(default_trace_path("dtc-scan")) as trace:
            for msg in iface.monitor(timeout=5.0):
                trace.log(msg)
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = can.BLFWriter(str(self.path))

    def log(self, message: can.Message) -> None:
        """Write a single frame to the trace."""
        self._writer(message)

    def close(self) -> None:
        """Flush and close the trace file."""
        self._writer.stop()

    def __enter__(self) -> BlfTraceLogger:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


def read_trace(path: str | Path) -> list[can.Message]:
    """Read a BLF trace back into a list of messages (handy for tests/replay)."""
    with can.BLFReader(str(path)) as reader:
        return list(reader)
