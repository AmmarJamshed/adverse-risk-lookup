"""Semantic risk matching and duplicate clustering."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Article, ArticleRiskMatch, Risk
from app.services.embedding_service import get_embeddings
from app.services.groq_service import get_groq

logger = get_logger("matching")


def match_article_to_risks(
    db: Session,
    article: Article,
    *,
    top_k: int = 5,
    min_similarity: float = 0.42,
    explain: bool = True,
) -> list[ArticleRiskMatch]:
    embeddings = get_embeddings()
    text = " ".join(
        filter(
            None,
            [
                article.title_en or article.title,
                article.summary_executive,
                article.content_en or article.content_original,
            ],
        )
    )
    if not article.embedding:
        article.embedding = embeddings.embed(text[:8000])
        db.commit()

    risks = db.query(Risk).filter(Risk.is_active.is_(True)).all()
    scored: list[tuple[Risk, float]] = []
    for risk in risks:
        if not risk.embedding:
            risk_text = f"{risk.name}. {risk.description or ''}. Category: {risk.category or ''}"
            risk.embedding = embeddings.embed(risk_text)
        score = embeddings.cosine(list(article.embedding), list(risk.embedding))
        if score >= min_similarity:
            scored.append((risk, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]
    matches: list[ArticleRiskMatch] = []

    # Clear previous matches for reprocessing
    db.query(ArticleRiskMatch).filter(ArticleRiskMatch.article_id == article.id).delete()

    for risk, score in top:
        explanation: dict = {}
        reasoning = None
        matched_concepts: list = []
        matched_controls: list = []
        affected_kris: list = []
        contributing_sentences: list = []
        contributing_words: list = []
        affected_departments: list = []
        confidence = min(1.0, score + 0.1)

        if explain and get_groq().api_key:
            try:
                explanation = get_groq().explain_match(
                    article_summary=article.summary_executive
                    or article.content_en
                    or article.title,
                    risk_name=risk.name,
                    risk_description=risk.description or "",
                    similarity=score,
                )
                reasoning = explanation.get("reasoning")
                matched_concepts = explanation.get("matched_concepts") or []
                matched_controls = explanation.get("matched_controls") or risk.controls or []
                affected_kris = explanation.get("affected_kris") or risk.kris or []
                contributing_sentences = explanation.get("contributing_sentences") or []
                contributing_words = explanation.get("contributing_words") or []
                affected_departments = explanation.get("affected_departments") or (
                    [risk.department] if risk.department else []
                )
                confidence = float(explanation.get("confidence") or confidence)
            except Exception as exc:
                logger.warning("explain_match_failed", error=str(exc))
                matched_controls = risk.controls or []
                affected_kris = risk.kris or []
                affected_departments = [risk.department] if risk.department else []
                reasoning = (
                    f"Semantic similarity {score:.2%} between article content and risk "
                    f"'{risk.name}' ({risk.category or 'uncategorized'})."
                )
        else:
            matched_controls = risk.controls or []
            affected_kris = risk.kris or []
            affected_departments = [risk.department] if risk.department else []
            reasoning = (
                f"Semantic similarity {score:.2%} between article content and risk "
                f"'{risk.name}'."
            )

        match = ArticleRiskMatch(
            article_id=article.id,
            risk_id=risk.id,
            similarity_score=score,
            confidence=confidence,
            reasoning=reasoning,
            matched_concepts=matched_concepts,
            matched_controls=matched_controls,
            affected_kris=affected_kris,
            contributing_sentences=contributing_sentences,
            contributing_words=contributing_words,
            affected_departments=affected_departments,
            explanation=explanation,
        )
        db.add(match)
        matches.append(match)

    db.commit()
    logger.info("risk_matching_done", article_id=str(article.id), matches=len(matches))
    return matches


def detect_duplicates(db: Session, article: Article, threshold: float = 0.92) -> Optional[Article]:
    embeddings = get_embeddings()
    if not article.embedding:
        text = f"{article.title_en or article.title} {article.content_en or ''}"
        article.embedding = embeddings.embed(text[:4000])
        db.commit()

    candidates = (
        db.query(Article)
        .filter(
            Article.id != article.id,
            Article.is_duplicate.is_(False),
            Article.is_relevant.is_(True),
            Article.embedding.isnot(None),
        )
        .order_by(Article.created_at.desc())
        .limit(200)
        .all()
    )
    best: Optional[Article] = None
    best_score = 0.0
    for other in candidates:
        score = embeddings.cosine(list(article.embedding), list(other.embedding))
        if score > best_score:
            best_score = score
            best = other

    if best and best_score >= threshold:
        article.is_duplicate = True
        article.master_article_id = best.id
        article.duplicate_confidence = best_score
        db.commit()
        logger.info(
            "duplicate_detected",
            article_id=str(article.id),
            master_id=str(best.id),
            confidence=best_score,
        )
        return best
    return None
