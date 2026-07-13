"""Risk register API."""

from typing import Optional
from uuid import UUID

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models import Risk, User
from app.schemas import RiskCreate, RiskOut
from app.services.embedding_service import get_embeddings
from app.services.risk_register_service import import_risks, preview_upload

router = APIRouter(prefix="/risks", tags=["Risk Register"])


@router.get("", response_model=list[RiskOut])
def list_risks(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("risks:read")),
):
    query = db.query(Risk).filter(Risk.is_active.is_(True))
    if q:
        query = query.filter(or_(Risk.name.ilike(f"%{q}%"), Risk.risk_id.ilike(f"%{q}%")))
    if category:
        query = query.filter(Risk.category.ilike(f"%{category}%"))
    return query.order_by(Risk.risk_id).limit(500).all()


@router.post("", response_model=RiskOut)
def create_risk(
    payload: RiskCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("risks:write")),
):
    emb = get_embeddings().embed(f"{payload.name}. {payload.description or ''}")
    risk = Risk(**payload.model_dump(), embedding=emb)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


@router.get("/{risk_id}", response_model=RiskOut)
def get_risk(
    risk_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("risks:read")),
):
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


@router.post("/upload/preview")
async def upload_preview(
    file: UploadFile = File(...),
    _: User = Depends(require_permission("risks:write")),
):
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 15MB)")
    return preview_upload(content, file.filename or "upload.csv")


@router.post("/upload/import")
async def upload_import(
    file: UploadFile = File(...),
    mapping: str = Form("{}"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("risks:write")),
):
    content = await file.read()
    try:
        mapping_dict = json.loads(mapping)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid mapping JSON") from exc
    return import_risks(db, content, file.filename or "upload.csv", mapping_dict)
