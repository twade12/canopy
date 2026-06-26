"""Signal-level decode of CAN frames via ``cantools`` (CLAUDE.md §4).

A loaded DBC turns raw arbitration-id + payload into named, scaled signals. This is the
foundation for restbus generation (Phase 1) and observation extraction (Phase 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import can
import cantools
from cantools.database import Database


@dataclass(slots=True)
class DecodedFrame:
    """A frame resolved against a DBC."""

    arbitration_id: int
    name: str
    signals: dict[str, object]


class Decoder:
    """Decodes :class:`can.Message` frames using one or more DBC files."""

    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_files(cls, *paths: str | Path) -> Decoder:
        """Load and merge one or more ``.dbc`` files into a single decoder."""
        if not paths:
            raise ValueError("at least one DBC path is required")
        db = cantools.database.Database()
        for path in paths:
            db.add_dbc_file(str(path))
        return cls(db)

    def decode(self, message: can.Message, *, decode_choices: bool = True) -> DecodedFrame | None:
        """Decode a frame, or return ``None`` if its ID is not in the DBC."""
        try:
            db_msg = self.db.get_message_by_frame_id(message.arbitration_id)
        except KeyError:
            return None
        signals = db_msg.decode(bytes(message.data), decode_choices=decode_choices)
        return DecodedFrame(
            arbitration_id=message.arbitration_id,
            name=db_msg.name,
            signals=dict(signals),
        )

    def format(self, message: can.Message) -> str:
        """Human-readable one-liner for a frame; falls back to raw hex if unknown."""
        decoded = self.decode(message)
        if decoded is None:
            return f"0x{message.arbitration_id:X}  <unknown>  {bytes(message.data).hex(' ')}"
        sigs = "  ".join(f"{k}={v}" for k, v in decoded.signals.items())
        return f"0x{decoded.arbitration_id:X}  {decoded.name}  {sigs}"
