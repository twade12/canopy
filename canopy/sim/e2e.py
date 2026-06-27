"""End-to-end (E2E) message protection: rolling alive-counters + checksums.

This is the make-or-break feature of a credible restbus (docs/ARCHITECTURE-NOTES.md §4).
Modern modules reject periodic frames whose alive-counter doesn't advance or whose
checksum/CRC doesn't validate (VW, GM, AUTOSAR E2E, …), and sit in a fault state. The
simulator must therefore *compute* these per frame.

The exact byte range and algorithm are OEM-specific, so both are pluggable. Counter and
checksum are addressed as DBC *signals*, so this works for any DBC-described message: we
set the counter, zero the checksum, encode, compute over the encoded bytes, write the
checksum back, and re-encode. The station's own verifier uses the identical convention,
so round-trips are self-consistent and testable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cantools.database.can import Message

ChecksumFn = Callable[[bytes], int]


def xor8(data: bytes) -> int:
    """8-bit XOR of all bytes."""
    acc = 0
    for b in data:
        acc ^= b
    return acc & 0xFF


def sum8(data: bytes) -> int:
    """8-bit additive checksum (sum of bytes mod 256)."""
    return sum(data) & 0xFF


def crc8_j1850(data: bytes) -> int:
    """CRC-8/SAE-J1850 (poly 0x1D, init 0xFF, xorout 0xFF) — AUTOSAR E2E Profile 1/2 base."""
    crc = 0xFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1D) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc ^ 0xFF


CHECKSUM_ALGORITHMS: dict[str, ChecksumFn] = {
    "xor8": xor8,
    "sum8": sum8,
    "crc8_j1850": crc8_j1850,
}


@dataclass(slots=True)
class E2EProfile:
    """Describes how a message is E2E-protected.

    Attributes:
        counter_signal: DBC signal carrying the rolling alive-counter (None = no counter).
        checksum_signal: DBC signal carrying the checksum (None = no checksum).
        algorithm: Key into :data:`CHECKSUM_ALGORITHMS`.
        counter_max: Counter wraps to 0 after this value (e.g. 15 for a 4-bit counter).
    """

    counter_signal: str | None = None
    checksum_signal: str | None = None
    algorithm: str = "sum8"
    counter_max: int = 15

    def checksum_fn(self) -> ChecksumFn:
        try:
            return CHECKSUM_ALGORITHMS[self.algorithm]
        except KeyError:
            raise ValueError(f"unknown checksum algorithm: {self.algorithm!r}") from None

    def encode(self, message: Message, signals: dict[str, object], counter: int) -> bytes:
        """Encode `signals` for `message`, injecting the alive-counter and checksum."""
        values = dict(signals)
        if self.counter_signal is not None:
            values[self.counter_signal] = counter % (self.counter_max + 1)
        if self.checksum_signal is None:
            return message.encode(values, strict=False)
        # Zero the checksum field, encode, compute over the wire bytes, write it back.
        values[self.checksum_signal] = 0
        data = message.encode(values, strict=False)
        values[self.checksum_signal] = self.checksum_fn()(data)
        return message.encode(values, strict=False)

    def verify(self, message: Message, data: bytes) -> bool:
        """True if `data`'s checksum field matches a recompute (counter not checked here)."""
        if self.checksum_signal is None:
            return True
        decoded = message.decode(data, decode_choices=False)
        claimed = int(decoded[self.checksum_signal])  # type: ignore[index]
        zeroed = dict(decoded)
        zeroed[self.checksum_signal] = 0
        recomputed = self.checksum_fn()(message.encode(zeroed, strict=False))
        return claimed == recomputed
