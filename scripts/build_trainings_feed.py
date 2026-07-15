"""
Build sanitized trainings feed from Eventbrite location listing pages
fetched via a browser-capable HTTP client (curl_cffi if available, else requests).

Writes the same outputs as scrape_trainings.py.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote_plus, urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scrape_trainings import (  # noqa: E402
    OUT_DIR,
    TRAINING_HINTS,
    clean_register_url,
    clean_text,
    enrich_from_html,
    event_id_from_url,
    parse_listing,
    write_outputs,
)

LOCATIONS = [
    ("Saudi Arabia", "saudi-arabia"),
    ("Bahrain", "bahrain"),
    ("Qatar", "qatar"),
    ("Oman", "oman"),
    ("Germany", "germany--berlin"),
    ("France", "france--paris"),
    ("Czech Republic", "czech-republic--prague"),
    ("Netherlands", "netherlands--amsterdam"),
    ("Canada", "canada--toronto"),
    ("Japan", "japan--tokyo"),
    ("Malaysia", "malaysia--kuala-lumpur"),
    ("Singapore", "singapore--singapore"),
]


def http_get(url: str) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        from curl_cffi import requests as creq

        r = creq.get(url, headers=headers, impersonate="chrome120", timeout=45)
        if r.status_code == 200:
            return r.text
        print(f"  curl_cffi HTTP {r.status_code}: {url}", flush=True)
    except Exception as exc:
        print(f"  curl_cffi unavailable/fail ({exc})", flush=True)

    try:
        import requests

        r = requests.get(url, headers=headers, timeout=45)
        if r.status_code == 200:
            return r.text
        print(f"  requests HTTP {r.status_code}: {url}", flush=True)
    except Exception as exc:
        print(f"  requests fail ({exc})", flush=True)
    return None


def fallback_search_url(country_slug: str, title: str) -> str:
    """Direct Eventbrite location search that surfaces the event for one-click open."""
    return f"https://www.eventbrite.com/d/{country_slug}/all-events/?q={quote_plus(title)}"


def main() -> int:
    by_url: dict[str, dict] = {}
    # Keep prior good /e/ links if present
    existing = OUT_DIR / "trainings.json"
    if existing.exists():
        try:
            for t in json.loads(existing.read_text(encoding="utf-8")).get("trainings") or []:
                u = clean_register_url(t.get("register_url") or "")
                if u and "/e/" in u:
                    by_url[u.rstrip("/")] = t
        except Exception:
            pass

    for country, slug in LOCATIONS:
        url = f"https://www.eventbrite.com/d/{slug}/all-events/?q=training"
        print(f"Fetch {country}: {url}", flush=True)
        html = http_get(url)
        time.sleep(2)
        if not html:
            continue
        events = parse_listing(html, country)
        print(f"  parsed {len(events)}", flush=True)
        for ev in events:
            if not TRAINING_HINTS.search(ev.get("title") or ""):
                continue
            reg = clean_register_url(ev.get("register_url") or "")
            if not reg or "/e/" not in reg:
                # Ensure users still land on a page that shows this training for registration
                reg = fallback_search_url(slug, ev["title"])
                ev["register_url"] = reg
                ev["register_mode"] = "search_landing"
            else:
                ev["register_mode"] = "event_page"
            # Enrich only real event pages
            if "/e/" in reg:
                detail = http_get(reg)
                time.sleep(1.2)
                if detail:
                    ev = enrich_from_html(ev, detail)
                    reg = clean_register_url(ev.get("register_url") or reg)
            key = reg.rstrip("/")
            by_url[key] = {
                "id": f"tr-{event_id_from_url(reg)}",
                "title": clean_text(ev.get("title"), 200),
                "description": clean_text(ev.get("description"), 800),
                "country": country,
                "city": clean_text(ev.get("city"), 80),
                "location_name": clean_text(ev.get("location_name"), 160),
                "organizer": clean_text(ev.get("organizer"), 120),
                "start_date": ev.get("start_date"),
                "end_date": ev.get("end_date"),
                "price": clean_text(ev.get("price"), 40),
                "register_url": reg,
                "source": "eventbrite",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

    out = list(by_url.values())
    out.sort(key=lambda e: (e.get("start_date") or "9999", e.get("country") or "", e.get("title") or ""))
    write_outputs(out)
    print(f"Countries: {sorted({e['country'] for e in out})}", flush=True)
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
