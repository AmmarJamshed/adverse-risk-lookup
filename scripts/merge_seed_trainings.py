"""Merge harvest_seed.json into the sanitized trainings feed (all output paths)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scrape_trainings import (  # noqa: E402
    JUNK_HINTS,
    clean_register_url,
    clean_text,
    ensure_description,
    event_id_from_url,
    write_outputs,
)

SEED = ROOT / "data" / "trainings" / "harvest_seed.json"
EXISTING = ROOT / "data" / "trainings" / "trainings.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(row: dict) -> dict | None:
    url = clean_register_url(row.get("register_url") or "")
    title = clean_text(row.get("title"), 200)
    description = clean_text(row.get("description"), 800)
    if not url or "/e/" not in url or len(title) < 6:
        return None
    if JUNK_HINTS.search(f"{title} {description}"):
        return None
    # Curated seed rows are pre-vetted; do not drop them on keyword mismatch.
    return ensure_description(
        {
            "id": f"tr-{event_id_from_url(url)}",
            "title": title,
            "description": description,
            "country": clean_text(row.get("country"), 80),
            "city": clean_text(row.get("city"), 80),
            "location_name": clean_text(row.get("location_name"), 160),
            "organizer": clean_text(row.get("organizer"), 120),
            "start_date": row.get("start_date") or None,
            "end_date": row.get("end_date") or None,
            "price": clean_text(row.get("price"), 40),
            "register_url": url,
            "source": clean_text(row.get("source") or "eventbrite", 40) or "eventbrite",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def main() -> int:
    by_url: dict[str, dict] = {}
    if EXISTING.exists():
        payload = load_json(EXISTING)
        for row in payload.get("trainings") or []:
            n = normalize(row)
            if n:
                by_url[n["register_url"].rstrip("/")] = n

    seed_rows = load_json(SEED) if SEED.exists() else []
    added = 0
    for row in seed_rows:
        n = normalize(row)
        if not n:
            print(f"skip invalid seed: {row.get('title')}", flush=True)
            continue
        key = n["register_url"].rstrip("/")
        if key not in by_url:
            added += 1
        # Prefer richer seed description/city when merging
        prev = by_url.get(key) or {}
        merged = {**prev, **{k: v for k, v in n.items() if v}}
        by_url[key] = merged

    events = list(by_url.values())
    events.sort(
        key=lambda e: (e.get("start_date") or "9999", e.get("country") or "", e.get("title") or "")
    )
    write_outputs(events)
    countries = sorted({e["country"] for e in events})
    print(f"Merged seed (+{added} new). Total {len(events)} across {countries}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
