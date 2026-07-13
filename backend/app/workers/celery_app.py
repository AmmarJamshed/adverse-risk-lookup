"""Celery application & scheduled workers."""

from __future__ import annotations

from datetime import datetime, timezone

from celery import Celery

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.models import Article, JobLog, RSSFeed
from app.services.news_service import collect_from_newsapi, collect_from_rss
from app.services.pipeline import process_article

configure_logging()
logger = get_logger("celery")
settings = get_settings()

celery_app = Celery(
    "arl",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    timezone=settings.celery_timezone,
    enable_utc=True,
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={
        "fetch-news-every-interval": {
            "task": "app.workers.tasks.fetch_all_news",
            "schedule": settings.news_fetch_interval_minutes * 60.0,
        },
        "process-pending-articles": {
            "task": "app.workers.tasks.process_pending_articles",
            "schedule": 120.0,
        },
    },
)


def _start_job(db, name: str) -> JobLog:
    job = JobLog(
        job_name=name,
        status="running",
        started_at=datetime.now(timezone.utc),
        details={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _finish_job(db, job: JobLog, status: str, details: dict | None = None, error: str | None = None):
    job.status = status
    job.finished_at = datetime.now(timezone.utc)
    if job.started_at:
        job.duration_ms = (job.finished_at - job.started_at).total_seconds() * 1000
    if details:
        job.details = details
    if error:
        job.error = error[:4000]
    db.commit()


@celery_app.task(name="app.workers.tasks.fetch_all_news", bind=True, max_retries=3)
def fetch_all_news(self):
    db = SessionLocal()
    job = _start_job(db, "fetch_all_news")
    try:
        newsapi_created = collect_from_newsapi(db)
        feeds = db.query(RSSFeed).filter(RSSFeed.is_active.is_(True)).all()
        rss_created = 0
        failures = 0
        for feed in feeds:
            try:
                rss_created += collect_from_rss(db, feed)
            except Exception:
                failures += 1
                logger.exception("feed_failed", feed_id=str(feed.id))
        details = {
            "newsapi_created": newsapi_created,
            "rss_created": rss_created,
            "feeds": len(feeds),
            "failures": failures,
        }
        _finish_job(db, job, "success", details)
        logger.info("fetch_all_news_done", **details)
        return details
    except Exception as exc:
        _finish_job(db, job, "failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.process_pending_articles")
def process_pending_articles(limit: int = 20):
    db = SessionLocal()
    job = _start_job(db, "process_pending_articles")
    processed = 0
    failed = 0
    try:
        pending = (
            db.query(Article)
            .filter(Article.processing_status == "pending")
            .order_by(Article.created_at.asc())
            .limit(limit)
            .all()
        )
        for article in pending:
            try:
                process_article(db, article.id)
                processed += 1
            except Exception:
                failed += 1
                logger.exception("article_process_failed", article_id=str(article.id))
        _finish_job(db, job, "success", {"processed": processed, "failed": failed})
        return {"processed": processed, "failed": failed}
    except Exception as exc:
        _finish_job(db, job, "failed", error=str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.process_one_article")
def process_one_article(article_id: str):
    db = SessionLocal()
    try:
        art = process_article(db, article_id)
        return {"id": str(art.id), "status": art.processing_status}
    finally:
        db.close()
