"""Run a sequence of commands and turn the results into a pass/fail report.

This is where *control* becomes *verified control*: each step sends a command, checks the
response, and (optionally) confirms a measured quantity is in range — e.g. "A/C clutch ON"
→ confirm current draw 4–8 A. The runner is transport-agnostic: callers pass an ``execute``
callback (runs one command spec → result dict) and a ``measure`` callback (quantity → value),
so it's testable with mocks and reusable by the bench API, the CLI, and the wiki export.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""
    response: str = ""
    measured: float | None = None

    def as_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail,
                "response": self.response, "measured": self.measured}


def run_sequence(
    steps: list[dict],
    execute: Callable[[dict], dict],
    measure: Callable[[str], float] | None = None,
) -> list[StepResult]:
    """Execute steps in order.

    Each step: ``{"name", "command": <spec>, "expect": {"positive": bool,
    "measure": {"quantity", "min", "max"}}}``. ``execute(spec)`` returns at least
    ``{"positive": bool, "summary": str, "response_hex": str}``.
    """
    results: list[StepResult] = []
    for step in steps:
        spec = step.get("command", {})
        expect = step.get("expect", {})
        res = execute(spec)
        want_positive = expect.get("positive", True)
        ok = bool(res.get("positive")) == bool(want_positive)
        detail = res.get("summary", "")
        measured: float | None = None
        meas = expect.get("measure")
        if ok and meas and measure is not None:
            measured = measure(meas["quantity"])
            lo, hi = meas.get("min"), meas.get("max")
            within = (lo is None or measured >= lo) and (hi is None or measured <= hi)
            ok = within
            rng = f"{lo if lo is not None else '−∞'}…{hi if hi is not None else '∞'}"
            detail += f" · {meas['quantity']}={measured} (want {rng}) → {'OK' if within else 'OUT'}"
        results.append(StepResult(
            name=step.get("name", spec.get("name", "step")), ok=ok, detail=detail,
            response=res.get("response_hex", ""), measured=measured))
    return results


def report_markdown(results: list[StepResult], title: str = "Bench verification") -> str:
    """Render a runner report as wiki-ready markdown."""
    passed = sum(1 for r in results if r.ok)
    lines = [f"## {title}", "", f"**{passed}/{len(results)} steps passed**", "",
             "| Step | Result | Detail |", "|---|---|---|"]
    for r in results:
        verdict = "✅ pass" if r.ok else "❌ fail"
        lines.append(f"| {r.name} | {verdict} | {r.detail or r.response} |")
    return "\n".join(lines) + "\n"
