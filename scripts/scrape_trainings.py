"""
Weekly training scraper for ARL (Playwright + Eventbrite JSON-LD).

Countries: Saudi Arabia, Bahrain, Qatar, Oman, Germany, France,
Czech Republic, Netherlands, Canada, Japan, Malaysia, Singapore.

Usage:
  python scripts/scrape_trainings.py
  python scripts/scrape_trainings.py --country "Singapore"
  python scripts/scrape_trainings.py --country Bahrain --country Qatar
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "trainings"
PUBLIC_OUT = ROOT / "frontend" / "public" / "data" / "trainings.json"
FUNC_OUT = ROOT / "frontend" / "netlify" / "functions" / "trainings-data.json"

LOCATIONS: list[dict[str, str]] = [
    {"country": "Saudi Arabia", "slug": "saudi-arabia"},
    {"country": "Bahrain", "slug": "bahrain"},
    {"country": "Qatar", "slug": "qatar"},
    {"country": "Oman", "slug": "oman"},
    {"country": "Germany", "slug": "germany--berlin"},
    {"country": "France", "slug": "france--paris"},
    {"country": "Czech Republic", "slug": "czech-republic--prague"},
    {"country": "Netherlands", "slug": "netherlands--amsterdam"},
    {"country": "Canada", "slug": "canada--toronto"},
    {"country": "Japan", "slug": "japan--tokyo"},
    {"country": "Malaysia", "slug": "malaysia--kuala-lumpur"},
    {"country": "Singapore", "slug": "singapore--singapore"},
]

QUERIES = ("training", "workshop", "course")

TRAINING_HINTS = re.compile(
    r"\b(training|workshop|course|certificate|certification|seminar|masterclass|"
    r"bootcamp|class|academy|cpd|cpe|professional development|"
    r"compliance|aml|risk management|governance|corporate course|"
    r"summit|conference|hackathon|summer school|camp|exam prep|prep)\b",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(value: str | None, max_len: int = 800) -> str:
    if not value:
        return ""
    text = unescape(str(value))
    text = TAG_RE.sub(" ", text).replace("\xa0", " ")
    text = WS_RE.sub(" ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return text


def clean_register_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(urljoin("https://www.eventbrite.com", url))
    path = parsed.path.split("?")[0]
    path = re.sub(r"/tickets-?\d*$", "", path)
    cleaned = urlunparse(
        (parsed.scheme or "https", parsed.netloc, path.rstrip("/") + "/", "", "", "")
    )
    return cleaned if "eventbrite." in cleaned else url.split("?")[0]


def event_id_from_url(url: str) -> str:
    m = re.search(r"-tickets-(\d+)", url) or re.search(r"/e/[^/]*-(\d+)", url)
    if m:
        return m.group(1)
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def listing_urls(slug: str) -> list[str]:
    # One listing URL per location to stay under Eventbrite rate limits
    return [f"https://www.eventbrite.com/d/{slug}/all-events/?q=training"]


def extract_jsonld_objects(html: str) -> list[dict[str, Any]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (tag.string or tag.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            out.extend([x for x in data if isinstance(x, dict)])
        elif isinstance(data, dict):
            if isinstance(data.get("@graph"), list):
                out.extend([x for x in data["@graph"] if isinstance(x, dict)])
            else:
                out.append(data)
    return out


def is_event(obj: dict[str, Any]) -> bool:
    t = obj.get("@type")
    return "Event" in t if isinstance(t, list) else t == "Event"


def parse_listing(html: str, country: str) -> list[dict[str, Any]]:
    from bs4 import BeautifulSoup

    found: list[dict[str, Any]] = []
    for obj in extract_jsonld_objects(html):
        if obj.get("@type") == "ItemList":
            for el in obj.get("itemListElement") or []:
                if not isinstance(el, dict):
                    continue
                item = el.get("item") if isinstance(el.get("item"), dict) else el
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or item.get("@id") or ""
                name = item.get("name") or ""
                if url and name:
                    found.append(
                        {
                            "title": clean_text(name, 200),
                            "register_url": clean_register_url(url),
                            "country": country,
                            "start_date": item.get("startDate"),
                            "end_date": item.get("endDate"),
                            "description": clean_text(item.get("description"), 400),
                            "city": "",
                            "location_name": "",
                            "organizer": "",
                            "source": "eventbrite",
                        }
                    )
        elif is_event(obj):
            url = obj.get("url") or obj.get("@id") or ""
            name = obj.get("name") or ""
            if url and name:
                found.append(
                    {
                        "title": clean_text(name, 200),
                        "register_url": clean_register_url(url),
                        "country": country,
                        "start_date": obj.get("startDate"),
                        "end_date": obj.get("endDate"),
                        "description": clean_text(obj.get("description"), 400),
                        "city": "",
                        "location_name": "",
                        "organizer": "",
                        "source": "eventbrite",
                    }
                )

    if not found:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href*='/e/']"):
            href = a.get("href") or ""
            title = clean_text(a.get_text(), 200)
            if "/e/" not in href or len(title) < 8:
                continue
            found.append(
                {
                    "title": title,
                    "register_url": clean_register_url(urljoin("https://www.eventbrite.com", href)),
                    "country": country,
                    "start_date": None,
                    "end_date": None,
                    "description": "",
                    "city": "",
                    "location_name": "",
                    "organizer": "",
                    "source": "eventbrite",
                }
            )
    return found


JUNK_HINTS = re.compile(
    r"\b(usa only|join whatsapp|whatsapp group|free\s+.*\busa\b)\b",
    re.I,
)


def looks_like_training(event: dict[str, Any]) -> bool:
    blob = f"{event.get('title', '')} {event.get('description', '')}"
    if JUNK_HINTS.search(blob):
        return False
    return bool(TRAINING_HINTS.search(blob))


def ensure_description(event: dict[str, Any]) -> dict[str, Any]:
    if not (event.get("description") or "").strip():
        title = clean_text(event.get("title"), 200)
        country = clean_text(event.get("country"), 80)
        event["description"] = clean_text(
            f"{title} — professional training listed for {country}." if country else title,
            800,
        )
    return event


def enrich_from_html(event: dict[str, Any], html: str) -> dict[str, Any]:
    for obj in extract_jsonld_objects(html):
        if not is_event(obj):
            continue
        event["title"] = clean_text(obj.get("name") or event["title"], 200)
        event["start_date"] = obj.get("startDate") or event.get("start_date")
        event["end_date"] = obj.get("endDate") or event.get("end_date")
        event["description"] = clean_text(obj.get("description") or event.get("description"), 800)
        if obj.get("url"):
            event["register_url"] = clean_register_url(obj["url"])
        org = obj.get("organizer")
        if isinstance(org, dict):
            event["organizer"] = clean_text(org.get("name"), 120)
        loc = obj.get("location")
        if isinstance(loc, dict):
            event["location_name"] = clean_text(loc.get("name"), 160)
            addr = loc.get("address")
            if isinstance(addr, dict):
                event["city"] = clean_text(addr.get("addressLocality"), 80)
        offers = obj.get("offers")
        if isinstance(offers, dict) and offers.get("url") and "/e/" in str(offers.get("url")):
            event["register_url"] = clean_register_url(offers["url"])
            if offers.get("price") is not None:
                event["price"] = clean_text(str(offers.get("price")), 40)
        break
    return event


def default_pause_ms(fallback: int = 3500) -> int:
    raw = os.environ.get("ARL_TRAININGS_PAUSE_MS", "").strip()
    if raw.isdigit():
        return max(1000, int(raw))
    return fallback


async def fetch_html(page, url: str, pause_ms: int | None = None) -> str | None:
    pause_ms = default_pause_ms(3500) if pause_ms is None else pause_ms
    try:
        await page.wait_for_timeout(pause_ms)
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        status = getattr(resp, "status", 0) or 0
        if status == 429:
            print(f"  rate-limited, backing off: {url}", flush=True)
            await page.wait_for_timeout(20000)
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            status = getattr(resp, "status", 0) or 0
        if not resp or status >= 400:
            print(f"  warn HTTP {status}: {url}", flush=True)
            return None
        await page.wait_for_timeout(1500)
        return await page.content()
    except Exception as exc:
        print(f"  warn fetch failed: {url} ({exc})", flush=True)
        return None


def ddg_event_urls(country: str, max_results: int = 12) -> list[dict[str, Any]]:
    """Discover Eventbrite event pages via DuckDuckGo HTML (avoids Eventbrite list 429s)."""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import unquote

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }
    )
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    queries = [
        f'site:eventbrite.com/e training OR workshop OR course "{country}"',
        f'site:eventbrite.com/e "{country}" certificate OR seminar OR compliance',
    ]
    for q in queries:
        try:
            r = session.post(
                "https://html.duckduckgo.com/html/",
                data={"q": q},
                timeout=30,
            )
        except requests.RequestException as exc:
            print(f"  ddg fail ({country}): {exc}", flush=True)
            continue
        if r.status_code != 200:
            print(f"  ddg HTTP {r.status_code} ({country})", flush=True)
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a.get("href") or ""
            # DDG wraps redirects: ...uddg=<urlencoded>
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = unquote(m.group(1))
            if "eventbrite." not in href or "/e/" not in href:
                continue
            url = clean_register_url(href)
            key = url.rstrip("/")
            if key in seen:
                continue
            title = clean_text(a.get_text(), 200)
            if not looks_like_training({"title": title, "description": ""}):
                continue
            seen.add(key)
            found.append(
                {
                    "title": title or "Training event",
                    "register_url": url,
                    "country": country,
                    "start_date": None,
                    "end_date": None,
                    "description": "",
                    "city": "",
                    "location_name": "",
                    "organizer": "",
                    "source": "eventbrite",
                }
            )
            if len(found) >= max_results:
                return found
        time.sleep(1.5)
    return found


def load_existing() -> dict[str, dict[str, Any]]:
    path = OUT_DIR / "trainings.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for t in payload.get("trainings") or []:
        url = clean_register_url(t.get("register_url") or "")
        if url:
            out[url.rstrip("/")] = t
    return out


def resolve_locations(countries: list[str] | None) -> list[dict[str, str]]:
    if not countries:
        return list(LOCATIONS)
    wanted = {c.strip().lower() for c in countries if c and c.strip()}
    matched = [loc for loc in LOCATIONS if loc["country"].lower() in wanted]
    known = {loc["country"].lower() for loc in LOCATIONS}
    unknown = sorted(wanted - known)
    if unknown:
        raise SystemExit(
            "Unknown country filter(s): "
            + ", ".join(unknown)
            + ". Expected one of: "
            + ", ".join(loc["country"] for loc in LOCATIONS)
        )
    if not matched:
        raise SystemExit("No countries matched filter.")
    return matched


async def scrape_all(
    max_per_country: int = 10,
    enrich_limit: int = 12,
    countries: list[str] | None = None,
) -> list[dict[str, Any]]:
    from playwright.async_api import async_playwright

    locations = resolve_locations(countries)
    scope = ", ".join(loc["country"] for loc in locations)
    print(f"Scraping countries: {scope}", flush=True)

    by_url = load_existing()
    print(f"Loaded {len(by_url)} existing trainings", flush=True)
    per_country: dict[str, int] = {}
    for ev in by_url.values():
        c = ev.get("country") or ""
        per_country[c] = per_country.get(c, 0) + 1

    listing_pause = default_pause_ms(12000)
    enrich_pause = max(3000, default_pause_ms(4000))

    # Soft discovery via DDG (often challenged; ignore failures)
    for loc in locations:
        country = loc["country"]
        print(f"Discovering {country} via search…", flush=True)
        for ev in ddg_event_urls(country, max_results=max_per_country):
            key = ev["register_url"].rstrip("/")
            if key not in by_url:
                by_url[key] = ev
                per_country[country] = per_country.get(country, 0) + 1
        print(f"  search total for {country}: {per_country.get(country, 0)}", flush=True)
        time.sleep(2.0)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1360, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await context.new_page()

        for loc in locations:
            country = loc["country"]
            slug = loc["slug"]
            print(f"Listing {country} ({slug})…", flush=True)
            for url in listing_urls(slug):
                html = await fetch_html(page, url, pause_ms=listing_pause)
                if not html:
                    continue
                for ev in parse_listing(html, country):
                    if not looks_like_training(ev):
                        continue
                    key = ev["register_url"].rstrip("/")
                    if not key or key in by_url:
                        continue
                    by_url[key] = ev
                    per_country[country] = per_country.get(country, 0) + 1
                    if per_country[country] >= max_per_country:
                        break
            print(f"  total for {country}: {per_country.get(country, 0)}", flush=True)

        # Enrich only sparse events for countries in this run
        scope_set = {loc["country"] for loc in locations}
        to_enrich = [
            e
            for e in by_url.values()
            if e.get("country") in scope_set and not (e.get("description") or "").strip()
        ]
        print(f"Enriching {min(len(to_enrich), enrich_limit)} sparse events…", flush=True)
        for ev in to_enrich[:enrich_limit]:
            html = await fetch_html(page, ev["register_url"], pause_ms=enrich_pause)
            if html:
                enriched = enrich_from_html(ev, html)
                by_url[enriched["register_url"].rstrip("/")] = enriched

        await context.close()
        await browser.close()

    enriched = list(by_url.values())
    out: list[dict[str, Any]] = []
    for ev in enriched:
        url = clean_register_url(ev.get("register_url") or "")
        title = clean_text(ev.get("title"), 200)
        if not url or "/e/" not in url or len(title) < 6:
            continue
        if not looks_like_training({"title": title, "description": ev.get("description") or ""}):
            continue
        row = ensure_description(
            {
                "id": f"tr-{event_id_from_url(url)}",
                "title": title,
                "description": clean_text(ev.get("description"), 800),
                "country": clean_text(ev.get("country"), 80),
                "city": clean_text(ev.get("city"), 80),
                "location_name": clean_text(ev.get("location_name"), 160),
                "organizer": clean_text(ev.get("organizer"), 120),
                "start_date": ev.get("start_date"),
                "end_date": ev.get("end_date"),
                "price": clean_text(ev.get("price"), 40),
                "register_url": url,
                "source": "eventbrite",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        out.append(row)

    out.sort(key=lambda e: (e.get("start_date") or "9999", e.get("country") or "", e.get("title") or ""))
    return out


def write_outputs(events: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUT.parent.mkdir(parents=True, exist_ok=True)
    FUNC_OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "countries": sorted({e["country"] for e in events}),
        "count": len(events),
        "trainings": events,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    (OUT_DIR / "trainings.json").write_text(text, encoding="utf-8")
    PUBLIC_OUT.write_text(text, encoding="utf-8")
    FUNC_OUT.write_text(text, encoding="utf-8")

    md = [
        "# Trainings (sanitized scrape)",
        "",
        f"Generated: {payload['generated_at']}",
        f"Total: {payload['count']}",
        "",
    ]
    for country in sorted({e["country"] for e in events}):
        md.append(f"## {country}")
        md.append("")
        for e in [x for x in events if x["country"] == country]:
            place = ", ".join([p for p in [e.get("city"), e.get("location_name")] if p]) or "Venue TBA"
            md.append(f"- **{e['title']}**")
            md.append(f"  - When: {e.get('start_date') or 'Date TBA'}")
            md.append(f"  - Where: {place}")
            if e.get("organizer"):
                md.append(f"  - Organizer: {e['organizer']}")
            if e.get("description"):
                md.append(f"  - {e['description']}")
            md.append(f"  - Register: {e['register_url']}")
            md.append("")
    (OUT_DIR / "TRAININGS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {len(events)} trainings -> {OUT_DIR / 'trainings.json'}", flush=True)


def merge_seed_file(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Always overlay verified seed registrations so sparse weekly scrapes keep coverage."""
    seed_path = OUT_DIR / "harvest_seed.json"
    if not seed_path.exists():
        return events
    try:
        seed_rows = json.loads(seed_path.read_text(encoding="utf-8"))
    except Exception:
        return events
    by_url = {clean_register_url(e.get("register_url") or "").rstrip("/"): e for e in events}
    for row in seed_rows or []:
        url = clean_register_url(row.get("register_url") or "")
        title = clean_text(row.get("title"), 200)
        description = clean_text(row.get("description"), 800)
        if not url or "/e/" not in url or len(title) < 6:
            continue
        if not looks_like_training({"title": title, "description": description}):
            continue
        key = url.rstrip("/")
        prev = by_url.get(key) or {}
        by_url[key] = {
            "id": f"tr-{event_id_from_url(url)}",
            "title": title or prev.get("title") or "",
            "description": description or prev.get("description") or "",
            "country": clean_text(row.get("country") or prev.get("country"), 80),
            "city": clean_text(row.get("city") or prev.get("city"), 80),
            "location_name": clean_text(row.get("location_name") or prev.get("location_name"), 160),
            "organizer": clean_text(row.get("organizer") or prev.get("organizer"), 120),
            "start_date": row.get("start_date") or prev.get("start_date"),
            "end_date": row.get("end_date") or prev.get("end_date"),
            "price": clean_text(row.get("price") or prev.get("price"), 40),
            "register_url": url,
            "source": "eventbrite",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
    out = list(by_url.values())
    out.sort(key=lambda e: (e.get("start_date") or "9999", e.get("country") or "", e.get("title") or ""))
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape and sanitize country trainings")
    parser.add_argument(
        "--country",
        action="append",
        dest="countries",
        metavar="NAME",
        help="Limit scrape to one country (repeatable). Default: all countries.",
    )
    return parser.parse_args(argv)


async def amain(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    events = await scrape_all(countries=args.countries)
    events = merge_seed_file(events)
    write_outputs(events)
    return 0 if events else 1


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(amain()))
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise
