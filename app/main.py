import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.endpoints.health import router as health_router
from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.schema_migrations import ensure_patient_portal_schema
from app.models.base import Base
from app.modules.patients.portal.auth_router import (
    router as patient_auth_router,
)
from app.modules.patients.portal.dashboard_router import (
    router as patient_dashboard_router,
)

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic owns schema changes outside local development. Keeping this
    # fallback makes a fresh developer database immediately usable.
    if settings.APP_ENV.lower() == "development":
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await ensure_patient_portal_schema(connection)

    logger.info("Application startup complete")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sri Sri Wellbeing Therapy Centre Management API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["x-request-id"] = request_id
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


# Canonical versioned API.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Compatibility aliases for clients currently using the unversioned API.
app.include_router(api_router, prefix="/api", include_in_schema=False)
app.include_router(health_router, include_in_schema=False)
app.include_router(
    patient_auth_router,
    prefix="/patient-auth",
    include_in_schema=False,
)
app.include_router(
    patient_dashboard_router,
    prefix="/patient",
    include_in_schema=False,
)


@app.get("/")
async def root() -> dict:
    return {
        "success": True,
        "message": "Welcome to Sri Sri Wellbeing API",
    }
