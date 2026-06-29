"""SecurityAccess (0x27) seed→key algorithms — a per-OEM plugin registry.

Unlocking actuation on a real ECU means answering its seed with the *right* key, computed
by an OEM-specific algorithm. Those algorithms are proprietary; this registry is the seam
where you drop one in (``register("ford_pcm_lvl1", fn)``) without touching the core. The
built-ins are generic/demo transforms — including ``xor_ff`` which matches the simulator.
"""

from __future__ import annotations

from collections.abc import Callable

KeyFn = Callable[[bytes], bytes]

_ALGOS: dict[str, KeyFn] = {}


def register(name: str, fn: KeyFn) -> None:
    _ALGOS[name] = fn


def get(name: str) -> KeyFn | None:
    return _ALGOS.get(name)


def names() -> list[str]:
    return sorted(_ALGOS)


# --- generic / demo algorithms ------------------------------------------------
register("echo", lambda seed: bytes(seed))                                  # returns seed (RE only)
register("xor_ff", lambda seed: bytes((b ^ 0xFF) & 0xFF for b in seed))     # matches the simulator
register("add_1", lambda seed: bytes((b + 1) & 0xFF for b in seed))
register("twos_complement", lambda seed: bytes((-b) & 0xFF for b in seed))


def _rotl_xor(seed: bytes, const: int = 0x5A) -> bytes:
    """Example of a typical OEM shape: rotate-left each byte, XOR a constant."""
    return bytes((((b << 1) | (b >> 7)) & 0xFF) ^ const for b in seed)


register("rotl_xor5a", _rotl_xor)
