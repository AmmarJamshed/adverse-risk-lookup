"""RSS feeds, dashboard, alerts, reports, admin, assistant."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_permission
from app.core.database import get_db
from app.core.security import hash_password, ROLE_PERMISSIONS
from app.models import (
    AlertSubscription,
    Article,
    AuditLog,
    EmergingRisk,
    JobLog,
    Notification,
    PromptTemplate,
    RSSFeed,
    User,
)
from app.schemas import (
    AlertCreate,
    AlertOut,
    AssistantRequest,
    AssistantResponse,
    FeedCreate,
    FeedOut,
    NotificationOut,
    UserCreate,
    UserOut,
)
from app.services.groq_service import get_groq
from app.services.news_service import collect_from_newsapi, collect_from_rss
from app.services.report_service import (
    build_dashboard_stats,
    generate_excel_report,
    generate_pdf_report,
    generate_word_report,
)

feeds_router = APIRouter(prefix="/feeds", tags=["RSS Feeds"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])
assistant_router = APIRouter(prefix="/assistant", tags=["AI Assistant"])
emerging_router = APIRouter(prefix="/emerging-risks", tags=["Emerging Risks"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@feeds_router.get("", response_model=list[FeedOut])
def list_feeds(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feeds:read")),
):
    return db.query(RSSFeed).order_by(RSSFeed.name).all()


@feeds_router.post("", response_model=FeedOut)
def create_feed(
    payload: FeedCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("feeds:write")),
):
    if db.query(RSSFeed).filter(RSSFeed.url == payload.url).first():
        raise HTTPException(status_code=400, detail="Feed URL already exists")
    feed = RSSFeed(**payload.model_dump())
    db.add(feed)
    db.commit()
    db.refresh(feed)
    log_audit(
        db,
        user_id=user.id,
        action="create_feed",
        resource_type="rss_feed",
        resource_id=str(feed.id),
        request=request,
    )
    return feed


@feeds_router.delete("/{feed_id}")
def delete_feed(
    feed_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feeds:write")),
):
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    db.delete(feed)
    db.commit()
    return {"ok": True}


@feeds_router.post("/{feed_id}/fetch")
def fetch_feed_now(
    feed_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feeds:write")),
):
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    created = collect_from_rss(db, feed)
    return {"created": created, "status": feed.last_status}


@feeds_router.post("/collect-newsapi")
def fetch_newsapi(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feeds:write")),
):
    created = collect_from_newsapi(db)
    return {"created": created}


@dashboard_router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return build_dashboard_stats(db)


@dashboard_router.get("/heatmap")
def risk_heatmap(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    articles = (
        db.query(Article)
        .filter(Article.is_relevant.is_(True), Article.country.isnot(None))
        .limit(500)
        .all()
    )
    cells: dict[str, dict[str, int]] = {}
    for a in articles:
        country = a.country or "Unknown"
        cat = a.risk_category or "Other"
        cells.setdefault(country, {})
        cells[country][cat] = cells[country].get(cat, 0) + 1
    return {"cells": cells}


@alerts_router.get("/subscriptions", response_model=list[AlertOut])
def list_subscriptions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("alerts:read")),
):
    return (
        db.query(AlertSubscription)
        .filter(AlertSubscription.user_id == user.id)
        .order_by(AlertSubscription.created_at.desc())
        .all()
    )


@alerts_router.post("/subscriptions", response_model=AlertOut)
def create_subscription(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("alerts:write")),
):
    sub = AlertSubscription(user_id=user.id, **payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@alerts_router.delete("/subscriptions/{sub_id}")
def delete_subscription(
    sub_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("alerts:write")),
):
    sub = (
        db.query(AlertSubscription)
        .filter(AlertSubscription.id == sub_id, AlertSubscription.user_id == user.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(sub)
    db.commit()
    return {"ok": True}


@notifications_router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    return q.order_by(Notification.created_at.desc()).limit(50).all()


@notifications_router.post("/{notification_id}/read")
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    n = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    n.is_read = True
    db.commit()
    return {"ok": True}


@reports_router.get("/pdf")
def report_pdf(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
):
    data = generate_pdf_report(db)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=arl-report.pdf"},
    )


@reports_router.get("/excel")
def report_excel(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
):
    data = generate_excel_report(db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=arl-report.xlsx"},
    )


@reports_router.get("/word")
def report_word(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
):
    data = generate_word_report(db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=arl-report.docx"},
    )


@emerging_router.get("")
def list_emerging(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("risks:read")),
):
    items = db.query(EmergingRisk).order_by(EmergingRisk.created_at.desc()).limit(50).all()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "description": i.description,
            "suggested_category": i.suggested_category,
            "suggested_owner": i.suggested_owner,
            "suggested_controls": i.suggested_controls,
            "confidence": i.confidence,
            "reasoning": i.reasoning,
            "trend_analysis": i.trend_analysis,
            "status": i.status,
            "article_count": len(i.article_ids or []),
        }
        for i in items
    ]


@assistant_router.post("", response_model=AssistantResponse)
def ask_assistant(
    payload: AssistantRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("assistant:use")),
):
    stats = build_dashboard_stats(db)
    recent = (
        db.query(Article)
        .filter(Article.is_relevant.is_(True))
        .order_by(Article.created_at.desc())
        .limit(15)
        .all()
    )
    context_lines = [
        f"Stats: {stats['totals']}",
        f"Top countries: {stats['countries'][:5]}",
        f"Categories: {stats['categories'][:5]}",
        "Recent articles:",
    ]
    for a in recent:
        context_lines.append(
            f"- [{a.severity}] {a.title_en or a.title} | {a.country} | {a.risk_category} | "
            f"{(a.summary_executive or '')[:160]}"
        )
    context = "\n".join(context_lines)
    if not get_groq().api_key:
        return AssistantResponse(
            answer=_local_assistant(payload.question, recent, stats),
            context_used=True,
        )
    answer = get_groq().assistant_reply(payload.question, context)
    return AssistantResponse(answer=answer)


def _local_assistant(question: str, articles: list[Article], stats: dict) -> str:
    q = question.lower()
    if "cyber" in q:
        items = [a for a in articles if "cyber" in (a.risk_category or "").lower() or "cyber" in " ".join(a.tags or [])]
        if not items:
            return "No recent cyber-related articles in the current dataset."
        lines = [f"• {a.title_en or a.title} ({a.severity})" for a in items[:5]]
        return "Recent cyber risks:\n" + "\n".join(lines)
    if "today" in q or "summary" in q:
        t = stats["totals"]
        return (
            f"Today's ARL snapshot — Relevant: {t['relevant']}, "
            f"Critical/High: {t['critical_alerts']}, Emerging: {t['emerging_risks']}."
        )
    return (
        f"Found {stats['totals']['relevant']} relevant articles. "
        f"Ask about cyber, AML, country, or request an executive summary."
    )


@admin_router.get("/users", response_model=list[UserOut])
def admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users:read")),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@admin_router.post("/users", response_model=UserOut)
def admin_create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users:write")),
):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email exists")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role if payload.role in ROLE_PERMISSIONS else "viewer",
        department=payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@admin_router.get("/audit-logs")
def audit_logs(
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("audit:read")),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at,
        }
        for l in logs
    ]


@admin_router.get("/jobs")
def job_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:read")),
):
    jobs = db.query(JobLog).order_by(JobLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": str(j.id),
            "job_name": j.job_name,
            "status": j.status,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "duration_ms": j.duration_ms,
            "details": j.details,
            "error": j.error,
        }
        for j in jobs
    ]


@admin_router.get("/prompts")
def list_prompts(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:read")),
):
    return [
        {"id": str(p.id), "key": p.key, "name": p.name, "description": p.description, "is_active": p.is_active}
        for p in db.query(PromptTemplate).all()
    ]


@admin_router.get("/roles")
def list_roles(_: User = Depends(require_permission("admin:read"))):
    return ROLE_PERMISSIONS
