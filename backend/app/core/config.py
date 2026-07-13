"""Adverse Risk Lookup (ARL) — Application settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Adverse Risk Lookup"
    app_env: str = "development"
    app_debug: bool = True
    app_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173"

    jwt_secret: str = Field(
        default="dev-only-change-me-jwt-secret-key",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    encryption_key: str = "change-me-fernet-key-32bytes!!"

    database_url: str = "postgresql+psycopg2://arl:arl_secure_password@localhost:5432/arl"
    redis_url: str = "redis://localhost:6379/0"

    news_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_translation_model: str = "llama-3.3-70b-versatile"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    use_faiss_fallback: bool = True

    appwrite_endpoint: str = "https://fra.cloud.appwrite.io/v1"
    appwrite_project_id: str = ""
    appwrite_api_key: str = ""
    appwrite_bucket_id: str = "arl-uploads"

    news_fetch_interval_minutes: int = 15
    celery_timezone: str = "UTC"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "arl-alerts@example.com"
    alerts_enabled: bool = False

    rate_limit_per_minute: int = 120
    log_level: str = "INFO"
    log_json: bool = False

    upload_dir: str = "uploads"
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "es", "ar", "ur", "hi"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _strip_origins(cls, v: str) -> str:
        return v or "http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
