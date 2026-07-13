"""Risk register CSV/Excel upload with intelligent column mapping."""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import Risk
from app.services.embedding_service import get_embeddings

logger = get_logger("risk_register")

CANONICAL_FIELDS = {
    "risk_id": ["risk id", "risk_id", "riskcode", "risk code", "ref", "id"],
    "name": ["risk name", "risk_name", "risk title", "title", "name"],
    "description": ["risk description", "description", "details", "narrative"],
    "category": ["risk category", "category", "risk type", "type"],
    "owner": ["risk owner", "owner", "accountable", "responsible"],
    "department": ["department", "dept", "business unit", "bu", "division"],
    "controls": ["key controls", "mitigating controls", "controls", "control"],
    "kris": ["key risk indicators", "kris", "kri", "indicators"],
    "residual_risk": ["residual risk", "residual rating", "residual"],
    "inherent_risk": ["inherent risk", "inherent rating", "inherent"],
    "risk_appetite": ["risk appetite", "appetite"],
    "treatment": ["risk treatment", "treatment", "response", "strategy"],
    "status": ["risk status", "status", "state"],
}


def suggest_column_mapping(columns: list[str]) -> dict[str, Optional[str]]:
    mapping: dict[str, Optional[str]] = {k: None for k in CANONICAL_FIELDS}
    used: set[str] = set()
    normalized = [(c, c.strip().lower()) for c in columns]

    # Pass 1: exact alias match (longest aliases preferred)
    for field, aliases in CANONICAL_FIELDS.items():
        for alias in sorted(aliases, key=len, reverse=True):
            for col, low in normalized:
                if col in used:
                    continue
                if low == alias:
                    mapping[field] = col
                    used.add(col)
                    break
            if mapping[field]:
                break

    # Pass 2: substring / contains for unmapped fields only
    for field, aliases in CANONICAL_FIELDS.items():
        if mapping[field]:
            continue
        for alias in sorted(aliases, key=len, reverse=True):
            if len(alias) < 4:
                continue
            for col, low in normalized:
                if col in used:
                    continue
                if alias in low or low in alias:
                    mapping[field] = col
                    used.add(col)
                    break
            if mapping[field]:
                break
    return mapping


def read_tabular(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    bio = io.BytesIO(file_bytes)
    if name.endswith(".csv"):
        return pd.read_csv(bio)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(bio)
    raise ValueError("Unsupported file type. Upload CSV or Excel.")


def preview_upload(file_bytes: bytes, filename: str) -> dict[str, Any]:
    df = read_tabular(file_bytes, filename)
    columns = [str(c) for c in df.columns.tolist()]
    sample = df.head(5).fillna("").astype(str).to_dict(orient="records")
    return {
        "columns": columns,
        "suggested_mapping": suggest_column_mapping(columns),
        "row_count": int(len(df)),
        "sample_rows": sample,
    }


def _split_list(value: Any) -> list:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    for sep in [";", "|", "\n"]:
        if sep in text:
            return [p.strip() for p in text.split(sep) if p.strip()]
    if "," in text and len(text) > 20:
        return [p.strip() for p in text.split(",") if p.strip()]
    return [text]


def import_risks(
    db: Session,
    file_bytes: bytes,
    filename: str,
    mapping: dict[str, str],
    organization_id=None,
) -> dict[str, Any]:
    df = read_tabular(file_bytes, filename)
    embeddings = get_embeddings()
    created = 0
    updated = 0

    for _, row in df.iterrows():
        def col(field: str) -> Any:
            src = mapping.get(field)
            if not src or src not in df.columns:
                return None
            val = row[src]
            if pd.isna(val):
                return None
            return val

        risk_code = str(col("risk_id") or f"AUTO-{created + updated + 1}")
        name = str(col("name") or "Unnamed Risk")
        description = str(col("description") or "") if col("description") is not None else ""

        existing = (
            db.query(Risk)
            .filter(Risk.risk_id == risk_code, Risk.organization_id == organization_id)
            .first()
        )
        payload = {
            "name": name[:500],
            "description": description,
            "category": str(col("category")) if col("category") is not None else None,
            "owner": str(col("owner")) if col("owner") is not None else None,
            "department": str(col("department")) if col("department") is not None else None,
            "controls": _split_list(col("controls")),
            "kris": _split_list(col("kris")),
            "residual_risk": str(col("residual_risk")) if col("residual_risk") is not None else None,
            "inherent_risk": str(col("inherent_risk")) if col("inherent_risk") is not None else None,
            "risk_appetite": str(col("risk_appetite")) if col("risk_appetite") is not None else None,
            "treatment": str(col("treatment")) if col("treatment") is not None else None,
            "status": str(col("status") or "open"),
        }
        embed_text = f"{name}. {description}. Category: {payload['category'] or ''}"
        vector = embeddings.embed(embed_text)

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            existing.embedding = vector
            updated += 1
        else:
            risk = Risk(
                organization_id=organization_id,
                risk_id=risk_code,
                embedding=vector,
                **payload,
            )
            db.add(risk)
            created += 1

    db.commit()
    logger.info("risk_register_import", created=created, updated=updated, file=filename)
    return {"created": created, "updated": updated, "total": created + updated}
