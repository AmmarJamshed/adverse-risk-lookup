"""Article processing pipeline: translate → AI analyze → embed → match → alerts."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Article, EmergingRisk, Notification, AlertSubscription
from app.services.embedding_service import get_embeddings
from app.services.groq_service import get_groq
from app.services.matching_service import detect_duplicates, match_article_to_risks
from app.services.translation_service import ensure_english

logger = get_logger("pipeline")


def process_article(db: Session, article_id) -> Article:
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise ValueError("Article not found")

    try:
        article.processing_status = "translating"
        db.commit()

        title_en, content_en, language, _ = ensure_english(
            article.title, article.content_original or ""
        )
        article.language = language
        article.title_en = title_en
        article.content_en = content_en

        article.processing_status = "analyzing"
        db.commit()

        analysis: dict = {}
        if get_groq().api_key:
            analysis = get_groq().analyze_article(title_en, content_en or title_en)
        else:
            analysis = _heuristic_analysis(title_en, content_en)

        article.is_relevant = bool(analysis.get("is_relevant", False))
        article.relevance_score = float(analysis.get("relevance_score") or 0)
        article.summary_executive = analysis.get("executive_summary")
        article.summary_detailed = analysis.get("detailed_summary")
        article.country = analysis.get("country")
        article.region = analysis.get("region")
        article.people = analysis.get("people") or []
        article.organizations = analysis.get("organizations") or []
        article.banks = analysis.get("banks") or []
        article.regulators = analysis.get("regulators") or []
        article.products = analysis.get("products") or []
        article.incident_type = analysis.get("incident_type")
        article.event_category = analysis.get("event_category")
        article.root_cause = analysis.get("root_cause")
        article.risk_category = analysis.get("risk_category")
        article.likelihood = _to_float(analysis.get("likelihood"))
        article.impact = _to_float(analysis.get("impact"))
        article.severity = analysis.get("severity")
        article.severity_score = float(analysis.get("severity_score") or 0)
        article.urgency = analysis.get("urgency")
        article.confidence = float(analysis.get("confidence") or 0)
        article.is_emerging = bool(analysis.get("is_emerging", False))
        article.requires_escalation = bool(analysis.get("requires_escalation", False))
        article.business_functions = analysis.get("business_functions") or []
        article.departments = analysis.get("departments") or []
        article.recommended_actions = analysis.get("recommended_actions") or {}
        article.suggested_controls = analysis.get("suggested_controls") or []
        article.affected_controls = analysis.get("affected_controls") or []
        article.committee_escalation = analysis.get("committee_escalation")
        article.tags = analysis.get("tags") or []
        article.ai_analysis = analysis

        if not article.is_relevant:
            article.processing_status = "skipped"
            db.commit()
            return article

        text_for_embed = f"{title_en}. {article.summary_executive or ''} {content_en or ''}"
        article.embedding = get_embeddings().embed(text_for_embed[:8000])
        db.commit()

        detect_duplicates(db, article)
        if article.is_duplicate:
            article.processing_status = "matched"
            db.commit()
            return article

        match_article_to_risks(db, article)
        article.processing_status = "matched"
        db.commit()

        evaluate_alerts(db, article)
        maybe_flag_emerging(db, article)
        return article
    except Exception as exc:
        logger.exception("pipeline_failed", article_id=str(article_id), error=str(exc))
        article.processing_status = "failed"
        db.commit()
        raise


def _to_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _heuristic_analysis(title: str, content: str) -> dict:
    text = f"{title} {content}".lower()
    keywords = [
        "bank",
        "fraud",
        "cyber",
        "aml",
        "sanction",
        "ransomware",
        "breach",
        "fintech",
        "payment",
        "regulator",
        "compliance",
    ]
    hits = sum(1 for k in keywords if k in text)
    relevant = hits >= 1
    severity = "high" if hits >= 3 else "medium" if hits >= 2 else "low"
    return {
        "is_relevant": relevant,
        "relevance_score": min(1.0, hits / 5),
        "executive_summary": title,
        "detailed_summary": (content or title)[:800],
        "country": None,
        "region": None,
        "people": [],
        "organizations": [],
        "banks": [],
        "regulators": [],
        "products": [],
        "incident_type": "adverse_media",
        "event_category": "operational",
        "root_cause": None,
        "risk_category": "Operational Risk",
        "likelihood": 3,
        "impact": 3 if relevant else 1,
        "severity": severity if relevant else "low",
        "severity_score": 70 if severity == "high" else 45 if severity == "medium" else 20,
        "urgency": "medium",
        "confidence": 0.4,
        "is_emerging": False,
        "requires_escalation": severity == "high",
        "business_functions": [],
        "departments": ["Operational Risk"],
        "recommended_actions": {
            "immediate": ["Review adverse media for institutional exposure"],
            "short_term": ["Map to risk register"],
            "long_term": ["Update monitoring rules"],
        },
        "suggested_controls": [],
        "affected_controls": [],
        "committee_escalation": None,
        "tags": [k for k in keywords if k in text],
    }


def evaluate_alerts(db: Session, article: Article) -> int:
    subs = db.query(AlertSubscription).filter(AlertSubscription.is_active.is_(True)).all()
    created = 0
    for sub in subs:
        if _subscription_matches(sub.conditions or {}, article):
            n = Notification(
                user_id=sub.user_id,
                title=f"Alert: {sub.name}",
                body=article.summary_executive or article.title,
                severity=article.severity or "info",
                link=f"/articles/{article.id}",
                metadata_json={"article_id": str(article.id), "subscription_id": str(sub.id)},
            )
            db.add(n)
            created += 1
    if created:
        db.commit()
    return created


def _subscription_matches(conditions: dict, article: Article) -> bool:
    if not conditions:
        return False
    severity_min = conditions.get("severity_min")
    if severity_min:
        order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if order.get((article.severity or "").lower(), 0) < order.get(
            str(severity_min).lower(), 0
        ):
            return False
    score_min = conditions.get("severity_score_min")
    if score_min is not None and (article.severity_score or 0) < float(score_min):
        return False
    country = conditions.get("country")
    if country and (article.country or "").lower() != str(country).lower():
        return False
    category = conditions.get("risk_category")
    if category and category.lower() not in (article.risk_category or "").lower():
        return False
    keyword = conditions.get("keyword")
    if keyword:
        blob = f"{article.title} {article.summary_executive or ''}".lower()
        if str(keyword).lower() not in blob:
            return False
    return True


def maybe_flag_emerging(db: Session, article: Article) -> None:
    if not article.is_emerging:
        return
    theme = (article.risk_category or article.incident_type or "emerging").lower().replace(
        " ", "_"
    )[:200]
    existing = db.query(EmergingRisk).filter(EmergingRisk.theme_key == theme).first()
    if existing:
        ids = list(existing.article_ids or [])
        if str(article.id) not in ids:
            ids.append(str(article.id))
            existing.article_ids = ids
            existing.trend_analysis = {
                **(existing.trend_analysis or {}),
                "count": len(ids),
                "last_seen": datetime.now(timezone.utc).isoformat(),
            }
            db.commit()
        return

    suggestion = {
        "title": f"Emerging: {article.risk_category or article.title[:80]}",
        "description": article.summary_executive,
        "suggested_category": article.risk_category,
        "suggested_owner": "Operational Risk",
        "suggested_controls": article.suggested_controls or [],
        "confidence": article.confidence,
        "reasoning": "Flagged by AI analysis as emerging theme",
        "trend_analysis": {"trajectory": "increasing", "count": 1},
    }
    if get_groq().api_key:
        try:
            suggestion = get_groq().suggest_emerging_risk(
                f"Theme: {theme}\nArticle: {article.summary_executive}\n"
                f"Category: {article.risk_category}\nTags: {article.tags}"
            )
        except Exception:
            pass

    er = EmergingRisk(
        title=suggestion.get("title") or theme,
        description=suggestion.get("description"),
        suggested_category=suggestion.get("suggested_category"),
        suggested_owner=suggestion.get("suggested_owner"),
        suggested_controls=suggestion.get("suggested_controls") or [],
        confidence=float(suggestion.get("confidence") or 0.5),
        reasoning=suggestion.get("reasoning"),
        trend_analysis=suggestion.get("trend_analysis") or {},
        article_ids=[str(article.id)],
        theme_key=theme,
    )
    db.add(er)
    db.commit()
