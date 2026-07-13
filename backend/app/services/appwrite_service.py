"""Optional Appwrite storage client (files / metadata sync)."""

from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("appwrite")


class AppwriteStorage:
    """Thin REST client for Appwrite Cloud file uploads.

    Note: Appwrite Databases are document stores — ARL uses PostgreSQL+pgvector
    as the system of record. Appwrite is used optionally for file binaries.
    """

    def __init__(self) -> None:
        s = get_settings()
        self.endpoint = s.appwrite_endpoint.rstrip("/")
        self.project_id = s.appwrite_project_id
        self.api_key = s.appwrite_api_key
        self.bucket_id = s.appwrite_bucket_id

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint and self.project_id and self.api_key)

    def _headers(self) -> dict:
        return {
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
        }

    def upload_bytes(self, filename: str, content: bytes, content_type: str = "application/octet-stream") -> Optional[dict]:
        if not self.enabled:
            logger.info("appwrite_skipped", reason="not_configured")
            return None
        url = f"{self.endpoint}/storage/buckets/{self.bucket_id}/files"
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    url,
                    headers=self._headers(),
                    files={"file": (filename, content, content_type)},
                    data={"fileId": "unique()"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("appwrite_upload_failed", error=str(exc))
            return None


_storage: Optional[AppwriteStorage] = None


def get_appwrite() -> AppwriteStorage:
    global _storage
    if _storage is None:
        _storage = AppwriteStorage()
    return _storage
