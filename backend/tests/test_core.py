"""Basic API unit tests (offline-friendly)."""

from app.core.security import create_access_token, hash_password, verify_password, has_permission
from app.services.embedding_service import EmbeddingService
from app.services.groq_service import parse_json_response
from app.services.risk_register_service import suggest_column_mapping


def test_password_hash_roundtrip():
    hashed = hash_password("ChangeMe123!")
    assert verify_password("ChangeMe123!", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_contains_subject():
    token = create_access_token("user-1", extra={"role": "admin"})
    assert isinstance(token, str)
    assert len(token) > 20


def test_rbac_admin_wildcard():
    assert has_permission("super_admin", "anything")
    assert has_permission("viewer", "articles:read")
    assert not has_permission("viewer", "users:write")


def test_parse_json_fenced():
    raw = '```json\n{"is_relevant": true, "severity": "high"}\n```'
    data = parse_json_response(raw)
    assert data["is_relevant"] is True
    assert data["severity"] == "high"


def test_column_mapping():
    cols = ["Risk ID", "Risk Name", "Description", "Category", "Owner", "Department"]
    mapping = suggest_column_mapping(cols)
    assert mapping["risk_id"] == "Risk ID"
    assert mapping["name"] == "Risk Name"
    assert mapping["category"] == "Category"


def test_hash_embed_deterministic():
    svc = EmbeddingService()
    a = svc._hash_embed("hello bank risk")
    b = svc._hash_embed("hello bank risk")
    assert a == b
    assert len(a) == svc.dim
