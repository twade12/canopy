"""Deep research: web + image search to fill knowledge gaps, with sourced links.

Finds things the local model can't know on its own — connector/harness photos, physical
pin layouts, OBD-II pinouts, protocol references — and returns them as **sourced results
with links** the technician can triage. Keyless scraping of search engines is unreliable
(anti-bot), so this uses a pluggable search API selected by whichever key is present:

  CANOPY_BRAVE_KEY    -> Brave Search API (web + images)   https://brave.com/search/api/
  CANOPY_TAVILY_KEY   -> Tavily AI search (web + images)   https://tavily.com/

If none is set, :func:`search` returns ``configured=False`` with setup guidance, so the UI
can prompt the operator. All results carry a source URL.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


def _get_json(url: str, headers: dict, timeout: float = 12) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def _post_json(url: str, payload: dict, timeout: float = 20) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def provider() -> str | None:
    if os.environ.get("CANOPY_BRAVE_KEY"):
        return "brave"
    if os.environ.get("CANOPY_TAVILY_KEY"):
        return "tavily"
    return None


def _brave(query: str, count: int) -> dict:
    key = os.environ["CANOPY_BRAVE_KEY"]
    headers = {"X-Subscription-Token": key, "Accept": "application/json"}
    q = urllib.parse.urlencode({"q": query, "count": count})
    web = _get_json(f"https://api.search.brave.com/res/v1/web/search?{q}", headers)
    results = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
        for r in web.get("web", {}).get("results", [])[:count]
    ]
    images = []
    try:
        img = _get_json(f"https://api.search.brave.com/res/v1/images/search?{q}", headers)
        for r in img.get("results", [])[:8]:
            images.append({
                "thumbnail": (r.get("thumbnail") or {}).get("src", ""),
                "image": (r.get("properties") or {}).get("url", ""),
                "source": r.get("url", ""),
                "title": r.get("title", ""),
            })
    except urllib.error.URLError:
        pass
    return {"results": results, "images": images}


def _tavily(query: str, count: int) -> dict:
    payload = {
        "api_key": os.environ["CANOPY_TAVILY_KEY"],
        "query": query,
        "max_results": count,
        "include_images": True,
    }
    data = _post_json("https://api.tavily.com/search", payload)
    results = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])[:count]
    ]
    images = [
        {"thumbnail": u, "image": u, "source": "", "title": ""}
        for u in data.get("images", [])[:8]
    ]
    return {"results": results, "images": images}


def search(query: str, *, count: int = 8) -> dict:
    """Run web+image search via the configured provider; sourced links always included."""
    prov = provider()
    if not prov:
        return {
            "configured": False,
            "provider": None,
            "results": [],
            "images": [],
            "hint": "Set CANOPY_BRAVE_KEY (brave.com/search/api) or CANOPY_TAVILY_KEY "
                    "(tavily.com) on the server to enable deep research.",
        }
    try:
        out = _brave(query, count) if prov == "brave" else _tavily(query, count)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        return {"configured": True, "provider": prov, "results": [], "images": [],
                "error": f"search failed: {e}"}
    return {"configured": True, "provider": prov, **out}
