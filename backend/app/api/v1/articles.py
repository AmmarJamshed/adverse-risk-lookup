"""Articles & global search API."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_permission
from app.core.database import get_db
from app.models import Article, ArticleRiskMatch, User
from app.schemas import ArticleDetail, ArticleOut

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("", response_model=list[ArticleOut])
def list_articles(
    q: Optional[str] = None,
    country: Optional[str] = None,
    bank: Optional[str] = None,
    language: Optional[str] = None,
    department: Optional[str] = None,
    regulator: Optional[str] = None,
    severity: Optional[str] = None,
    risk_category: Optional[str] = None,
    tag: Optional[str] = None,
    emerging: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("articles:read")),
):
    query = db.query(Article).filter(
        Article.is_relevant.is_(True),
        Article.is_duplicate.is_(False),
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Article.title.ilike(like),
                Article.title_en.ilike(like),
                Article.summary_executive.ilike(like),
                Article.content_en.ilike(like),
            )
        )
    if country:
        query = query.filter(Article.country.ilike(f"%{country}%"))
    if language:
        query = query.filter(Article.language == language)
    if severity:
        query = query.filter(Article.severity == severity.lower())
    if risk_category:
        query = query.filter(Article.risk_category.ilike(f"%{risk_category}%"))
    if emerging is not None:
        query = query.filter(Article.is_emerging.is_(emerging))
    articles = (
        query.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    # JSON-field filters applied in Python for portability across PG versions
    results = []
    for a in articles:
        if bank and bank.lower() not in " ".join(a.banks or []).lower():
            continue
        if department and department.lower() not in " ".join(a.departments or []).lower():
            continue
        if regulator and regulator.lower() not in " ".join(a.regulators or []).lower():
            continue
        if tag and tag.lower() not in " ".join(a.tags or []).lower():
            continue
        results.append(a)
    return results


@router.get("/{article_id}", response_model=ArticleDetail)
def get_article(
    article_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("articles:read")),
):
    article = (
        db.query(Article)
        .options(joinedload(Article.risk_matches).joinedload(ArticleRiskMatch.risk))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    detail = ArticleDetail.model_validate(article)
    detail.risk_matches = [
        {
            "id": str(m.id),
            "risk_id": str(m.risk_id),
            "risk_code": m.risk.risk_id if m.risk else None,
            "risk_name": m.risk.name if m.risk else None,
            "similarity_score": m.similarity_score,
            "confidence": m.confidence,
            "reasoning": m.reasoning,
            "matched_concepts": m.matched_concepts,
            "matched_controls": m.matched_controls,
            "affected_kris": m.affected_kris,
            "contributing_sentences": m.contributing_sentences,
            "contributing_words": m.contributing_words,
            "affected_departments": m.affected_departments,
            "explanation": m.explanation,
        }
        for m in article.risk_matches
    ]
    return detail


@router.post("/{article_id}/reprocess")
def reprocess(
    article_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("articles:write")),
):
    from app.services.pipeline import process_article

    article = process_article(db, article_id)
    return {"id": str(article.id), "status": article.processing_status}
