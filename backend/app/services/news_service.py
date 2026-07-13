"""NewsAPI and RSS collection engines."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import feedparser
import httpx
from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import Article, RSSFeed

logger = get_logger("news")


BANKING_QUERY = (
    "bank OR banking OR fintech OR AML OR KYC OR fraud OR cybersecurity OR "
    '"operational risk" OR sanctions OR Basel OR CBDC OR "payment systems" OR '
    '"money laundering" OR "central bank" OR DORA OR "open banking"'
)


def url_hash(url: str) -> str:
    normalized = url.strip().lower().rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    try:
        dt = date_parser.parse(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError, OverflowError):
        return None


class NewsAPIClient:
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self) -> None:
        self.api_key = get_settings().news_api_key

    def fetch_everything(self, query: str = BANKING_QUERY, page_size: int = 50) -> list[dict]:
        if not self.api_key:
            logger.warning("newsapi_key_missing")
            return []
        params = {
            "q": query,
            "language": None,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.api_key,
        }
        # NewsAPI rejects null language — drop empty keys
        params = {k: v for k, v in params.items() if v is not None}
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(f"{self.BASE_URL}/everything", params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("articles", [])
        except Exception as exc:
            logger.error("newsapi_fetch_failed", error=str(exc))
            return []


class RSSEngine:
    def fetch_feed(self, feed: RSSFeed) -> list[dict]:
        logger.info("rss_fetch_start", feed=feed.name, url=feed.url)
        try:
            parsed = feedparser.parse(feed.url)
            if getattr(parsed, "bozo", False) and not parsed.entries:
                raise RuntimeError(str(getattr(parsed, "bozo_exception", "parse error")))
            entries = []
            for entry in parsed.entries[:100]:
                link = entry.get("link") or entry.get("id") or ""
                title = entry.get("title") or "Untitled"
                summary = entry.get("summary") or entry.get("description") or ""
                published = (
                    entry.get("published")
                    or entry.get("updated")
                    or entry.get("created")
                )
                entries.append(
                    {
                        "title": title,
                        "url": link,
                        "content": summary,
                        "published_at": published,
                        "source_name": feed.name,
                    }
                )
            logger.info("rss_fetch_done", feed=feed.name, count=len(entries))
            return entries
        except Exception as exc:
            logger.error("rss_fetch_failed", feed=feed.name, error=str(exc))
            raise


def upsert_raw_article(
    db: Session,
    *,
    title: str,
    url: str,
    content: str,
    source_type: str,
    source_name: Optional[str] = None,
    feed_id: Optional[Any] = None,
    published_at: Any = None,
) -> Optional[Article]:
    if not url:
        host = urlparse(source_name or "unknown").netloc or "unknown"
        url = f"urn:{host}:{url_hash(title + content[:200])}"
    h = url_hash(url)
    existing = db.query(Article).filter(Article.url_hash == h).first()
    if existing:
        return None
    article = Article(
        title=title[:1000],
        url=url[:2000],
        url_hash=h,
        content_original=content,
        source_type=source_type,
        source_name=source_name,
        feed_id=feed_id,
        published_at=parse_datetime(published_at),
        processing_status="pending",
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def collect_from_newsapi(db: Session) -> int:
    client = NewsAPIClient()
    articles = client.fetch_everything()
    created = 0
    for item in articles:
        art = upsert_raw_article(
            db,
            title=item.get("title") or "Untitled",
            url=item.get("url") or "",
            content=item.get("description") or item.get("content") or "",
            source_type="newsapi",
            source_name=(item.get("source") or {}).get("name"),
            published_at=item.get("publishedAt"),
        )
        if art:
            created += 1
    logger.info("newsapi_ingest_done", created=created, fetched=len(articles))
    return created


def collect_from_rss(db: Session, feed: RSSFeed) -> int:
    engine = RSSEngine()
    try:
        entries = engine.fetch_feed(feed)
        created = 0
        for item in entries:
            art = upsert_raw_article(
                db,
                title=item["title"],
                url=item["url"],
                content=item["content"],
                source_type="rss",
                source_name=item.get("source_name"),
                feed_id=feed.id,
                published_at=item.get("published_at"),
            )
            if art:
                created += 1
        feed.last_fetched_at = datetime.now(timezone.utc)
        feed.last_status = "success"
        feed.last_error = None
        feed.success_count = (feed.success_count or 0) + 1
        db.commit()
        return created
    except Exception as exc:
        feed.last_fetched_at = datetime.now(timezone.utc)
        feed.last_status = "failed"
        feed.last_error = str(exc)[:2000]
        feed.failure_count = (feed.failure_count or 0) + 1
        db.commit()
        return 0
