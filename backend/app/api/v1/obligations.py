"""Regulatory obligations workflow API — horizon → applicability → register → gap cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.models import (
    ControlItem,
    GapCase,
    HorizonItem,
    Obligation,
    PolicyDoc,
    RegulatorySource,
    User,
)

router = APIRouter(tags=["Regulatory Obligations"])


class ApplicabilityIn(BaseModel):
    horizon_id: UUID
    candidate_id: str
    decision: str
    rationale: Optional[str] = None


class MappingIn(BaseModel):
    kind: str = "policy"
    ref_id: UUID
    coverage: str = "partial"
    notes: str = ""
    gap_status: Optional[str] = None
    remediation_notes: Optional[str] = None


class SourceIn(BaseModel):
    name: str
    url: str
    regulator: str = ""
    jurisdiction: str = ""
    category: str = "general"


class CasePatch(BaseModel):
    status: Optional[str] = None
    gap_status: Optional[str] = None
    remediation_notes: Optional[str] = None


def _obl_code(jurisdiction: str, db: Session) -> str:
    prefix = {"UK": "UK", "USA": "US", "EU": "EU", "Pakistan": "PK"}.get(jurisdiction, "XX")
    count = db.query(Obligation).count() + 1
    return f"OBL-{prefix}-{count:03d}"


def _case_number(db: Session) -> str:
    count = db.query(GapCase).count() + 1
    return f"GAP-2024-{count:04d}"


def _serialize_horizon(h: HorizonItem) -> dict[str, Any]:
    return {
        "id": str(h.id),
        "title": h.title,
        "jurisdiction": h.jurisdiction,
        "regulator": h.regulator,
        "instrument_type": h.instrument_type,
        "reference": h.reference,
        "published_at": h.published_at.isoformat() if h.published_at else None,
        "summary": h.summary,
        "body": h.body,
        "source_id": str(h.source_id) if h.source_id else None,
        "source_name": h.source_name,
        "status": h.status,
        "priority": h.priority,
        "tags": h.tags or [],
        "candidates": h.candidates or [],
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


def _serialize_obligation(o: Obligation) -> dict[str, Any]:
    return {
        "id": str(o.id),
        "code": o.code,
        "statement": o.statement,
        "jurisdiction": o.jurisdiction,
        "regulator": o.regulator,
        "theme": o.theme,
        "owner": o.owner,
        "status": o.status,
        "source_horizon_id": str(o.source_horizon_id) if o.source_horizon_id else None,
        "source_candidate_id": o.source_candidate_id,
        "source_reference": o.source_reference,
        "due_date": o.due_date,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _serialize_case(c: GapCase, obligation: Optional[Obligation] = None) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "case_number": c.case_number,
        "obligation_id": str(c.obligation_id),
        "title": c.title,
        "status": c.status,
        "gap_status": c.gap_status,
        "owner": c.owner,
        "jurisdiction": c.jurisdiction,
        "remediation_notes": c.remediation_notes or "",
        "mappings": c.mappings or [],
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "obligation": _serialize_obligation(obligation) if obligation else None,
    }





@router.get("/sources")
def list_sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(RegulatorySource).order_by(RegulatorySource.name).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "regulator": s.regulator,
            "jurisdiction": s.jurisdiction,
            "url": s.url,
            "category": s.category,
            "is_active": s.is_active,
            "last_status": s.last_status,
            "success_count": s.success_count,
            "failure_count": s.failure_count,
        }
        for s in rows
    ]


@router.post("/sources")
def create_source(
    payload: SourceIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("feeds:write")),
):
    row = RegulatorySource(
        name=payload.name,
        url=payload.url,
        regulator=payload.regulator,
        jurisdiction=payload.jurisdiction,
        category=payload.category,
        last_status="created",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": str(row.id),
        "name": row.name,
        "regulator": row.regulator,
        "jurisdiction": row.jurisdiction,
        "url": row.url,
        "category": row.category,
        "is_active": row.is_active,
        "last_status": row.last_status,
        "success_count": row.success_count,
        "failure_count": row.failure_count,
    }


@router.get("/horizon")
def list_horizon(
    jurisdiction: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(HorizonItem)
    if jurisdiction:
        query = query.filter(HorizonItem.jurisdiction == jurisdiction)
    if status:
        query = query.filter(HorizonItem.status == status)
    rows = query.order_by(HorizonItem.created_at.desc()).all()
    if q:
        ql = q.lower()
        rows = [
            h
            for h in rows
            if ql in h.title.lower()
            or ql in (h.summary or "").lower()
            or ql in (h.reference or "").lower()
        ]
    return [_serialize_horizon(h) for h in rows]


@router.get("/horizon/{item_id}")
def get_horizon(item_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    h = db.query(HorizonItem).filter(HorizonItem.id == item_id).first()
    if not h:
        raise HTTPException(404, "Not found")
    return _serialize_horizon(h)


@router.get("/applicability")
def applicability_inbox(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    inbox = []
    for h in db.query(HorizonItem).all():
        for c in h.candidates or []:
            if status and c.get("applicability") != status:
                continue
            inbox.append(
                {
                    "horizon_id": str(h.id),
                    "horizon_title": h.title,
                    "jurisdiction": h.jurisdiction,
                    "regulator": h.regulator,
                    "reference": h.reference,
                    "priority": h.priority,
                    "candidate": c,
                }
            )
    return inbox


@router.post("/applicability")
def set_applicability(
    payload: ApplicabilityIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    decision = payload.decision.lower()
    if decision not in ("applicable", "not_applicable", "under_review"):
        raise HTTPException(400, "decision must be applicable | not_applicable | under_review")
    h = db.query(HorizonItem).filter(HorizonItem.id == payload.horizon_id).first()
    if not h:
        raise HTTPException(404, "Horizon item not found")
    candidates = list(h.candidates or [])
    cand = next((c for c in candidates if c.get("id") == payload.candidate_id), None)
    if not cand:
        raise HTTPException(404, "Candidate not found")

    cand["applicability"] = decision
    if payload.rationale:
        cand["rationale"] = payload.rationale
    cand["assessed_by"] = user.full_name
    cand["assessed_at"] = datetime.now(timezone.utc).isoformat()
    h.candidates = candidates

    if all(c.get("applicability") != "under_review" for c in candidates):
        h.status = "assessed"
    elif h.status == "pending_assessment":
        h.status = "in_assessment"

    obligation = None
    gap_case = None
    if decision == "applicable":
        existing = (
            db.query(Obligation)
            .filter(
                Obligation.source_horizon_id == h.id,
                Obligation.source_candidate_id == payload.candidate_id,
            )
            .first()
        )
        if existing:
            obligation = existing
            gap_case = db.query(GapCase).filter(GapCase.obligation_id == existing.id).first()
        else:
            obligation = Obligation(
                code=_obl_code(h.jurisdiction, db),
                statement=cand.get("text") or "",
                jurisdiction=h.jurisdiction,
                regulator=h.regulator,
                theme=cand.get("theme"),
                owner=cand.get("suggested_owner") or "Compliance",
                status="open",
                source_horizon_id=h.id,
                source_candidate_id=payload.candidate_id,
                source_reference=h.reference,
                due_date=(datetime.now(timezone.utc) + timedelta(days=90)).date().isoformat(),
            )
            db.add(obligation)
            db.flush()
            gap_case = GapCase(
                case_number=_case_number(db),
                obligation_id=obligation.id,
                title=f"Gap analysis — {cand.get('theme') or obligation.code}",
                status="open",
                gap_status="gap",
                owner=obligation.owner,
                jurisdiction=obligation.jurisdiction,
                remediation_notes="",
                mappings=[],
            )
            db.add(gap_case)

    db.commit()
    if obligation:
        db.refresh(obligation)
    if gap_case:
        db.refresh(gap_case)

    return {
        "item": _serialize_horizon(h),
        "candidate": cand,
        "obligation": _serialize_obligation(obligation) if obligation else None,
        "gap_case": _serialize_case(gap_case, obligation) if gap_case else None,
    }


@router.get("/obligations")
def list_obligations(
    jurisdiction: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Obligation)
    if jurisdiction:
        q = q.filter(Obligation.jurisdiction == jurisdiction)
    if status:
        q = q.filter(Obligation.status == status)
    return [_serialize_obligation(o) for o in q.order_by(Obligation.created_at.desc()).all()]


@router.get("/obligations/{obl_id}")
def get_obligation(obl_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    o = db.query(Obligation).filter(Obligation.id == obl_id).first()
    if not o:
        raise HTTPException(404, "Not found")
    return _serialize_obligation(o)


@router.get("/policies")
def list_policies(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [
        {
            "id": str(p.id),
            "code": p.code,
            "title": p.title,
            "owner": p.owner,
            "jurisdiction": p.jurisdiction,
            "status": p.status,
            "summary": p.summary,
        }
        for p in db.query(PolicyDoc).order_by(PolicyDoc.code).all()
    ]


@router.get("/controls")
def list_controls(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [
        {
            "id": str(c.id),
            "code": c.code,
            "title": c.title,
            "policy_id": str(c.policy_id) if c.policy_id else None,
            "owner": c.owner,
            "type": c.type,
            "status": c.status,
        }
        for c in db.query(ControlItem).order_by(ControlItem.code).all()
    ]


@router.get("/library")
def library(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    policies = [
        {
            "id": str(p.id),
            "code": p.code,
            "title": p.title,
            "owner": p.owner,
            "jurisdiction": p.jurisdiction,
            "status": p.status,
            "summary": p.summary,
        }
        for p in db.query(PolicyDoc).order_by(PolicyDoc.code).all()
    ]
    controls = [
        {
            "id": str(c.id),
            "code": c.code,
            "title": c.title,
            "policy_id": str(c.policy_id) if c.policy_id else None,
            "owner": c.owner,
            "type": c.type,
            "status": c.status,
        }
        for c in db.query(ControlItem).order_by(ControlItem.code).all()
    ]
    return {"policies": policies, "controls": controls}

@router.get("/cases")
def list_cases(
    jurisdiction: Optional[str] = None,
    gap_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(GapCase)
    if jurisdiction:
        q = q.filter(GapCase.jurisdiction == jurisdiction)
    if gap_status:
        q = q.filter(GapCase.gap_status == gap_status)
    if status:
        q = q.filter(GapCase.status == status)
    out = []
    for c in q.order_by(GapCase.created_at.desc()).all():
        obl = db.query(Obligation).filter(Obligation.id == c.obligation_id).first()
        out.append(_serialize_case(c, obl))
    return out


@router.get("/cases/{case_id}")
def get_case(case_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    c = db.query(GapCase).filter(GapCase.id == case_id).first()
    if not c:
        raise HTTPException(404, "Not found")
    obl = db.query(Obligation).filter(Obligation.id == c.obligation_id).first()
    return _serialize_case(c, obl)


@router.post("/cases/{case_id}/mappings")
def add_mapping(
    case_id: UUID,
    payload: MappingIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.query(GapCase).filter(GapCase.id == case_id).first()
    if not c:
        raise HTTPException(404, "Not found")
    kind = "control" if payload.kind == "control" else "policy"
    if kind == "policy":
        ref = db.query(PolicyDoc).filter(PolicyDoc.id == payload.ref_id).first()
    else:
        ref = db.query(ControlItem).filter(ControlItem.id == payload.ref_id).first()
    if not ref:
        raise HTTPException(400, "ref_id not found in library")
    mapping = {
        "id": str(uuid4()),
        "kind": kind,
        "ref_id": str(ref.id),
        "ref_code": ref.code,
        "ref_title": ref.title,
        "coverage": payload.coverage,
        "notes": payload.notes,
    }
    mappings = list(c.mappings or [])
    mappings.append(mapping)
    c.mappings = mappings
    if payload.gap_status:
        c.gap_status = payload.gap_status
    else:
        coverages = [m.get("coverage") for m in mappings]
        if all(x == "mapped" for x in coverages):
            c.gap_status = "mapped"
        elif any(x == "gap" for x in coverages):
            c.gap_status = "gap"
        else:
            c.gap_status = "partial"
    if payload.remediation_notes is not None:
        c.remediation_notes = payload.remediation_notes
    if c.status == "open":
        c.status = "in_progress"
    db.commit()
    db.refresh(c)
    obl = db.query(Obligation).filter(Obligation.id == c.obligation_id).first()
    return _serialize_case(c, obl)


@router.patch("/cases/{case_id}")
def patch_case(
    case_id: UUID,
    payload: CasePatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = db.query(GapCase).filter(GapCase.id == case_id).first()
    if not c:
        raise HTTPException(404, "Not found")
    if payload.status:
        c.status = payload.status
    if payload.gap_status:
        c.gap_status = payload.gap_status
    if payload.remediation_notes is not None:
        c.remediation_notes = payload.remediation_notes
    db.commit()
    db.refresh(c)
    return _serialize_case(c)
