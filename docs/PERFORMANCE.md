# Measuring Canopy performance

`scripts/bench.py` is a repeatable benchmark that seeds a realistic database, starts a real
uvicorn server, hammers the hot endpoints, and reports **p50/p95 latency** and **on-the-wire
bytes** — plus the **delta vs the last run**, so you can see performance move as the platform
changes. (LLM endpoints are excluded — they depend on Ollama and aren't deterministic.)

## Run it
```bash
.venv/bin/python scripts/bench.py                      # 100 projects, 60 runs/endpoint
.venv/bin/python scripts/bench.py --vehicles 300 --runs 80   # heavier, shows index scaling
.venv/bin/python scripts/bench.py --baseline           # save THIS run as the comparison point
```
Each run appends to `.bench/history.jsonl`; `--baseline` (or the first run) writes `.bench/last.json`,
which subsequent runs diff against (the `Δp50` column).

## What it measures and what "better" looks like
| Row | What it proves |
|---|---|
| `static/app.js (gzip)` etc. | transport size after **gzip** — smaller `bytes` = faster first load |
| `attachment image (200)` vs `(304)` | the **ETag cache**: the 304 row should be ~0 bytes and faster — that's the re-render/thumbnail win |
| `GET /api/knowledge` | shows the `Cache-Control` header (browser/`api.cget` can skip refetches) |
| `GET /api/vehicles`, `/{id}`, `pcb-components`, `wiki` | endpoint latency **at scale** (run with `--vehicles 300` to watch the DB indexes hold latency flat as data grows) |

Lower `p50`/`p95` and smaller `bytes` are better. To compare a change: run `--baseline` on the old
code, make the change, run again — the `Δp50` column shows the per-endpoint movement.

## Measuring the front-end too
The script covers transport + backend. For SPA render/interaction timing, use Chrome DevTools →
Performance/Network on the live app (watch DOMContentLoaded, the gzipped `app.js` size, and that
attachment images return `304`/`(disk cache)` on revisits). The client-side `api.cget` cache means
flipping tabs/projects should issue **no** repeat network calls for the project list, the open
project, or the knowledge base within the TTL.
