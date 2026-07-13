"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=8)
    role: str = "viewer"
    department: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool
    preferences: dict = {}

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: UUID
    title: str
    title_en: Optional[str] = None
    url: str
    source_type: str
    source_name: Optional[str] = None
    language: str
    country: Optional[str] = None
    region: Optional[str] = None
    published_at: Optional[datetime] = None
    summary_executive: Optional[str] = None
    summary_detailed: Optional[str] = None
    content_original: Optional[str] = None
    content_en: Optional[str] = None
    severity: Optional[str] = None
    severity_score: float = 0
    urgency: Optional[str] = None
    confidence: float = 0
    is_relevant: bool = False
    is_emerging: bool = False
    requires_escalation: bool = False
    risk_category: Optional[str] = None
    incident_type: Optional[str] = None
    banks: list = []
    regulators: list = []
    departments: list = []
    tags: list = []
    recommended_actions: dict = {}
    processing_status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleOut):
    people: list = []
    organizations: list = []
    products: list = []
    root_cause: Optional[str] = None
    suggested_controls: list = []
    affected_controls: list = []
    committee_escalation: Optional[str] = None
    ai_analysis: dict = {}
    risk_matches: list[dict] = []


class RiskOut(BaseModel):
    id: UUID
    risk_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    department: Optional[str] = None
    controls: list = []
    kris: list = []
    residual_risk: Optional[str] = None
    inherent_risk: Optional[str] = None
    risk_appetite: Optional[str] = None
    treatment: Optional[str] = None
    status: str
    is_active: bool = True

    model_config = {"from_attributes": True}


class RiskCreate(BaseModel):
    risk_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    department: Optional[str] = None
    controls: list = []
    kris: list = []
    residual_risk: Optional[str] = None
    inherent_risk: Optional[str] = None
    risk_appetite: Optional[str] = None
    treatment: Optional[str] = None
    status: str = "open"


class FeedCreate(BaseModel):
    name: str
    url: str
    category: str = "financial"
    language: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True


class FeedOut(BaseModel):
    id: UUID
    name: str
    url: str
    category: str
    language: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0

    model_config = {"from_attributes": True}


class AlertCreate(BaseModel):
    name: str
    conditions: dict[str, Any]
    channels: list[str] = ["dashboard"]
    is_active: bool = True


class AlertOut(BaseModel):
    id: UUID
    name: str
    conditions: dict
    channels: list
    is_active: bool

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: UUID
    title: str
    body: str
    severity: str
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AssistantResponse(BaseModel):
    answer: str
    context_used: bool = True


class ColumnMappingRequest(BaseModel):
    mapping: dict[str, str]


class SearchParams(BaseModel):
    q: Optional[str] = None
    country: Optional[str] = None
    bank: Optional[str] = None
    language: Optional[str] = None
    department: Optional[str] = None
    regulator: Optional[str] = None
    severity: Optional[str] = None
    risk_category: Optional[str] = None
    tag: Optional[str] = None
    emerging: Optional[bool] = None
    skip: int = 0
    limit: int = 25
