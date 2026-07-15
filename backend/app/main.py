"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.api.v1 import (
    admin_router,
    alerts_router,
    assistant_router,
    dashboard_router,
    emerging_router,
    feeds_router,
    notifications_router,
    reports_router,
)
from app.api.v1.articles import router as articles_router
from app.api.v1.auth import router as auth_router
from app.api.v1.risks import router as risks_router
from app.core.config import get_settings
from app.core.database import Base, engine, init_vector_extension
from app.core.logging import RequestLoggingMiddleware, configure_logging, get_logger

configure_logging()
logger = get_logger("main")
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("arl_starting", version=__version__, env=settings.app_env)
    with engine.begin() as conn:
        init_vector_extension(conn)
        Base.metadata.create_all(bind=conn)
    yield
    logger.info("arl_shutdown")


app = FastAPI(
    title="Adverse Risk Lookup (ARL)",
    description="AI-Powered Banking Adverse Media & Risk Intelligence Platform",
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

api = FastAPI()
# Mount under /api for Netlify proxy friendliness
app.include_router(auth_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")
app.include_router(risks_router, prefix="/api/v1")
app.include_router(feeds_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")
app.include_router(emerging_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Adverse Risk Lookup",
        "version": __version__,
        "tagline": "Transforming Global Banking News into Actionable Risk Intelligence",
    }


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
