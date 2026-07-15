"""SQLAlchemy ORM models for ARL."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base

try:
    from pgvector.sqlalchemy import Vector

    _PGVECTOR_IMPORT = True
except ImportError:
    _PGVECTOR_IMPORT = False
    Vector = None  # type: ignore

_USE_PGVECTOR = _PGVECTOR_IMPORT and os.getenv("DATABASE_URL", "").startswith("postgresql")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


JSONType = JSON().with_variant(JSONB(), "postgresql")
EmbeddingType = Vector(384) if _USE_PGVECTOR else JSONType


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str] = mapped_column(String(100), default="bank")
    country: Mapped[Optional[str]] = mapped_column(String(100))
    settings: Mapped[dict] = mapped_column(JSONType, default=dict)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    risks: Mapped[list["Risk"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferences: Mapped[dict] = mapped_column(JSONType, default=dict)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    organization: Mapped[Optional[Organization]] = relationship(back_populates="users")
    alert_subscriptions: Mapped[list["AlertSubscription"]] = relationship(
        back_populates="user"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSONType, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class RSSFeed(Base, TimestampMixin):
    __tablename__ = "rss_feeds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="financial")
    language: Mapped[Optional[str]] = mapped_column(String(10))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[Optional[str]] = mapped_column(String(50))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict)


class Article(Base, TimestampMixin):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_articles_url_hash"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_severity", "severity"),
        Index("ix_articles_language", "language"),
        Index("ix_articles_country", "country"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    source_type: Mapped[str] = mapped_column(String(50), default="rss")  # rss | newsapi | manual
    source_name: Mapped[Optional[str]] = mapped_column(String(255))
    feed_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("rss_feeds.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(1000))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_original: Mapped[Optional[str]] = mapped_column(Text)
    content_en: Mapped[Optional[str]] = mapped_column(Text)
    summary_executive: Mapped[Optional[str]] = mapped_column(Text)
    summary_detailed: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en")
    country: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    master_article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("articles.id"), nullable=True
    )
    duplicate_confidence: Mapped[Optional[float]] = mapped_column(Float)
    processing_status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # pending|translating|analyzing|matched|failed|skipped
    severity: Mapped[Optional[str]] = mapped_column(String(20))  # critical|high|medium|low
    severity_score: Mapped[float] = mapped_column(Float, default=0.0)
    urgency: Mapped[Optional[str]] = mapped_column(String(20))
    likelihood: Mapped[Optional[float]] = mapped_column(Float)
    impact: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_emerging: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    requires_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    incident_type: Mapped[Optional[str]] = mapped_column(String(100))
    event_category: Mapped[Optional[str]] = mapped_column(String(100))
    risk_category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    people: Mapped[list] = mapped_column(JSONType, default=list)
    organizations: Mapped[list] = mapped_column(JSONType, default=list)
    banks: Mapped[list] = mapped_column(JSONType, default=list)
    regulators: Mapped[list] = mapped_column(JSONType, default=list)
    products: Mapped[list] = mapped_column(JSONType, default=list)
    departments: Mapped[list] = mapped_column(JSONType, default=list)
    business_functions: Mapped[list] = mapped_column(JSONType, default=list)
    recommended_actions: Mapped[dict] = mapped_column(JSONType, default=dict)
    suggested_controls: Mapped[list] = mapped_column(JSONType, default=list)
    affected_controls: Mapped[list] = mapped_column(JSONType, default=list)
    committee_escalation: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSONType, default=list)
    ai_analysis: Mapped[dict] = mapped_column(JSONType, default=dict)
    embedding: Mapped[Optional[Any]] = mapped_column(
        EmbeddingType, nullable=True
    )

    risk_matches: Mapped[list["ArticleRiskMatch"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )


class Risk(Base, TimestampMixin):
    __tablename__ = "risks"
    __table_args__ = (Index("ix_risks_category", "category"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=True
    )
    risk_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    owner: Mapped[Optional[str]] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    controls: Mapped[list] = mapped_column(JSONType, default=list)
    kris: Mapped[list] = mapped_column(JSONType, default=list)
    residual_risk: Mapped[Optional[str]] = mapped_column(String(50))
    inherent_risk: Mapped[Optional[str]] = mapped_column(String(50))
    risk_appetite: Mapped[Optional[str]] = mapped_column(String(100))
    treatment: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="open")
    extra_fields: Mapped[dict] = mapped_column(JSONType, default=dict)
    embedding: Mapped[Optional[Any]] = mapped_column(
        EmbeddingType, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped[Optional[Organization]] = relationship(back_populates="risks")
    matches: Mapped[list["ArticleRiskMatch"]] = relationship(back_populates="risk")


class ArticleRiskMatch(Base, TimestampMixin):
    __tablename__ = "article_risk_matches"
    __table_args__ = (
        UniqueConstraint("article_id", "risk_id", name="uq_article_risk"),
        Index("ix_matches_similarity", "similarity_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("articles.id"), nullable=False
    )
    risk_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("risks.id"), nullable=False
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    matched_concepts: Mapped[list] = mapped_column(JSONType, default=list)
    matched_controls: Mapped[list] = mapped_column(JSONType, default=list)
    affected_kris: Mapped[list] = mapped_column(JSONType, default=list)
    contributing_sentences: Mapped[list] = mapped_column(JSONType, default=list)
    contributing_words: Mapped[list] = mapped_column(JSONType, default=list)
    affected_departments: Mapped[list] = mapped_column(JSONType, default=list)
    explanation: Mapped[dict] = mapped_column(JSONType, default=dict)

    article: Mapped[Article] = relationship(back_populates="risk_matches")
    risk: Mapped[Risk] = relationship(back_populates="matches")


class EmergingRisk(Base, TimestampMixin):
    __tablename__ = "emerging_risks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    suggested_category: Mapped[Optional[str]] = mapped_column(String(100))
    suggested_owner: Mapped[Optional[str]] = mapped_column(String(255))
    suggested_controls: Mapped[list] = mapped_column(JSONType, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    trend_analysis: Mapped[dict] = mapped_column(JSONType, default=dict)
    article_ids: Mapped[list] = mapped_column(JSONType, default=list)
    theme_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="recommended")


class AlertSubscription(Base, TimestampMixin):
    __tablename__ = "alert_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    conditions: Mapped[dict] = mapped_column(JSONType, default=dict)
    channels: Mapped[list] = mapped_column(JSONType, default=lambda: ["dashboard"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="alert_subscriptions")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    link: Mapped[Optional[str]] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict)


class JobLog(Base, TimestampMixin):
    __tablename__ = "job_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    job_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[Optional[float]] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSONType, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text)


class PromptTemplate(Base, TimestampMixin):
    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONType, default=dict)
    description: Mapped[Optional[str]] = mapped_column(Text)
