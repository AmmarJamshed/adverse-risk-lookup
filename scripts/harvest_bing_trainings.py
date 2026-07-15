"""Discover Eventbrite /e/ training URLs via Bing (fallback when Eventbrite lists 429)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "trainings" / "_bing_urls.json"

COUNTRIES = {
    "Singapore": 'Singapore',
    "Malaysia": 'Malaysia OR "Kuala Lumpur"',
    "Canada": "Canada OR Toronto",
    "Japan": "Japan OR Tokyo",
    "Netherlands": "Netherlands OR Amsterdam",
    "Saudi Arabia": '"Saudi Arabia" OR Riyadh OR Jeddah',
    "Bahrain": "Bahrain OR Manama",
    "Qatar": "Qatar OR Doha",
    "Oman": "Oman OR Muscat",
    "Germany": "Germany OR Berlin",
    "France": "France OR Paris",
    "Czech Republic": '"Czech Republic" OR Prague',
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

URL_RE = re.compile(
    r"https?://(?:www\.)?eventbrite\.[a-z.]+/e/[a-zA-Z0-9\-]+(?:-tickets-\d+)?/?",
    re.I,
)


def clean_url(url: str) -> str:
    url = url.split("&")[0].split("?")[0]
    if not url.endswith("/"):
        url += "/"
    return url


def search_country(country: str, locq: str) -> list[str]:
    q = f"site:eventbrite.com/e ({locq}) (training OR workshop OR course OR certification)"
    url = "https://www.bing.com/search?q=" + quote_plus(q) + "&count=30"
    print(f"QUERY {country}", flush=True)
    r = requests.get(url, headers=UA, timeout=30)
    print(f"  status {r.status_code} len {len(r.text)}", flush=True)
    found = sorted({clean_url(u) for u in URL_RE.findall(r.text)})
    print(f"  found {len(found)}", flush=True)
    for u in found[:10]:
        print(f"   {u}", flush=True)
    return found


def main() -> int:
    all_found: dict[str, list[str]] = {}
    for country, locq in COUNTRIES.items():
        all_found[country] = search_country(country, locq)
        time.sleep(2.5)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(all_found, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
