#!/usr/bin/env python3
"""CANOPY performance benchmark — measure HTTP latency, payload sizes, and cache wins.

Spins up a real uvicorn server against a freshly-seeded SQLite database, hits the hot
endpoints many times, and reports p50/p95 latency + on-the-wire bytes. It records a baseline
to .bench/last.json and prints the delta vs the previous run, so you can see performance move as
the platform changes.

Usage:
    .venv/bin/python scripts/bench.py                 # default scale
    .venv/bin/python scripts/bench.py --vehicles 200 --runs 80
    .venv/bin/python scripts/bench.py --baseline      # save this run as the comparison baseline

Excludes LLM endpoints (Ollama-dependent / non-deterministic). Set CANOPY_WARM=0 automatically.
"""

from __future__ import annotations

import argparse
import contextlib
import http.client
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / ".bench"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def seed(data_dir: str, n_vehicles: int) -> dict:
    """Populate a realistic DB directly through the store (fast)."""
    sys.path.insert(0, str(ROOT))
    from PIL import Image

    from canopy.vision.store import Store
    db = str(Path(data_dir) / "canopy_vision.db")  # must match VisionConfig.db_path
    s = Store(db)
    up = Path(data_dir) / "uploads"
    up.mkdir(parents=True, exist_ok=True)
    img = up / "board.png"
    Image.new("RGB", (1200, 800), (10, 90, 50)).save(img)
    first_vid = first_aid = None
    for i in range(n_vehicles):
        v = s.create_vehicle(label=f"Module {i}", make="GM", model="TCM", year="2012")
        vid = v["id"]
        s.add_tag(vid, "TCM")
        s.merge_pinouts(vid, None, 0, [
            {"connector": "C1", "pin": str(p), "signal": f"SIG{p}", "function": f"fn {p}"}
            for p in range(24)])
        aid = s.add_attachment(vid, str(img), kind="pcb")["id"]
        s.replace_pcb_components(vid, aid, [
            {"label": f"U{c}", "box": [0.1, 0.1, 0.2, 0.2], "function": "ic",
             "check": "rails", "part": "", "confidence": 0.8} for c in range(10)])
        for m in range(5):
            s.add_measurement(vid, kind="dmm", label=f"rail {m}", mode="vdc", value=5.0, unit="V")
        if first_vid is None:
            first_vid, first_aid = vid, aid
    return {"db": db, "vid": first_vid, "aid": first_aid}


@contextlib.contextmanager
def server(data_dir: str):
    port = free_port()
    env = {**os.environ, "CANOPY_VISION_DATA": data_dir, "CANOPY_WARM": "0"}
    env.pop("CANOPY_PASSWORD", None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "--factory", "canopy.vision.app:create_app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        env=env, cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                c = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                c.request("GET", "/healthz")
                c.getresponse().read()
                c.close()
                break
            except OSError:
                time.sleep(0.1)
        yield port
    finally:
        proc.terminate()
        with contextlib.suppress(Exception):
            proc.wait(timeout=5)


def request(port: int, path: str, headers: dict | None = None) -> tuple[float, int, int, dict]:
    """Return (ms, status, wire_bytes, response_headers) for one GET."""
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    t0 = time.perf_counter()
    c.request("GET", path, headers=headers or {})
    r = c.getresponse()
    body = r.read()
    ms = (time.perf_counter() - t0) * 1000
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    c.close()
    return ms, r.status, len(body), hdrs


def bench(port: int, path: str, runs: int, headers: dict | None = None) -> dict:
    ms, status, nbytes, hdrs = [], None, 0, {}
    for _ in range(runs):
        t, st, b, h = request(port, path, headers)
        ms.append(t)
        status, nbytes, hdrs = st, b, h
    ms.sort()

    def p(q):
        return ms[min(len(ms) - 1, int(len(ms) * q))]
    return {"p50": round(statistics.median(ms), 2), "p95": round(p(0.95), 2),
            "min": round(ms[0], 2), "bytes": nbytes, "status": status,
            "cache": hdrs.get("cache-control", ""), "enc": hdrs.get("content-encoding", "")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vehicles", type=int, default=100)
    ap.add_argument("--runs", type=int, default=60)
    ap.add_argument("--baseline", action="store_true", help="save this run as the baseline")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as data_dir:
        print(f"seeding {args.vehicles} projects…", file=sys.stderr)
        ids = seed(data_dir, args.vehicles)
        gz = {"Accept-Encoding": "gzip"}
        with server(data_dir) as port:
            vid, aid = ids["vid"], ids["aid"]
            etag = request(port, f"/api/attachment/{aid}/image")[3].get("etag", "")
            cases = {
                "static/app.js (gzip)": ("/static/app.js", gz),
                "static/style.css (gzip)": ("/static/style.css", gz),
                "index.html (gzip)": ("/", gz),
                "GET /api/vehicles (list)": ("/api/vehicles", gz),
                "GET /api/vehicles/{id}": (f"/api/vehicles/{vid}", gz),
                "GET pcb-components": (f"/api/vehicles/{vid}/pcb-components", gz),
                "GET memories": (f"/api/vehicles/{vid}/memories", gz),
                "GET wiki (compiled)": (f"/api/vehicles/{vid}/wiki", gz),
                "GET /api/knowledge": ("/api/knowledge", gz),
                "attachment image (200)": (f"/api/attachment/{aid}/image", None),
                "attachment image (304)": (f"/api/attachment/{aid}/image", {"If-None-Match": etag}),
            }
            results = {name: bench(port, path, args.runs, h) for name, (path, h) in cases.items()}

    prev = {}
    last = BENCH_DIR / "last.json"
    if last.exists():
        prev = json.loads(last.read_text()).get("results", {})

    print(f"\nCANOPY benchmark — {args.vehicles} projects, {args.runs} runs/endpoint\n")
    print(f"{'endpoint':<28}{'p50 ms':>9}{'p95 ms':>9}{'bytes':>10}{'Δp50':>9}  notes")
    print("-" * 88)
    for name, r in results.items():
        delta = ""
        if name in prev:
            d = r["p50"] - prev[name]["p50"]
            delta = f"{d:+.1f}"
        note = " ".join(filter(None, [r["enc"], r["cache"], f"HTTP{r['status']}"
                                      if r["status"] not in (200,) else ""]))
        print(f"{name:<28}{r['p50']:>9}{r['p95']:>9}{r['bytes']:>10}{delta:>9}  {note}")

    BENCH_DIR.mkdir(exist_ok=True)
    payload = {"ts": time.time(), "vehicles": args.vehicles, "runs": args.runs, "results": results}
    (BENCH_DIR / "history.jsonl").open("a").write(json.dumps(payload) + "\n")
    if args.baseline or not last.exists():
        last.write_text(json.dumps(payload, indent=2))
        print("\n(saved as baseline → .bench/last.json)")
    else:
        print("\n(Δp50 vs .bench/last.json — rerun with --baseline to update it)")


if __name__ == "__main__":
    main()
