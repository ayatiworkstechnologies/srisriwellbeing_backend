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

from app.modules.appointments.router import (
    appointments_router,
    doctor_availability_router,
)


# =========================================================
# LOGGING
# =========================================================

configure_logging(settings.LOG_LEVEL)

logger = logging.getLogger(__name__)


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Alembic owns schema changes outside local development.
    # This fallback allows a fresh local developer database
    # to create tables automatically.

    if settings.APP_ENV.lower() == "development":

        async with engine.begin() as connection:

            await connection.run_sync(
                Base.metadata.create_all
            )

            await ensure_patient_portal_schema(
                connection
            )

    logger.info(
        "Application startup complete"
    )

    yield

    await engine.dispose()


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Sri Sri Wellbeing Therapy Centre "
        "Management API"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# EXCEPTION HANDLERS
# =========================================================

register_exception_handlers(app)


# =========================================================
# REQUEST LOGGING MIDDLEWARE
# =========================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):

    request_id = request.headers.get(
        "x-request-id",
        str(uuid.uuid4()),
    )

    started_at = time.perf_counter()

    response = await call_next(
        request
    )

    duration_ms = round(
        (
            time.perf_counter()
            - started_at
        )
        * 1000,
        2,
    )

    response.headers[
        "x-request-id"
    ] = request_id

    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": (
                response.status_code
            ),
            "duration_ms": duration_ms,
        },
    )

    return response


# =========================================================
# MAIN VERSIONED API
# =========================================================

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


# =========================================================
# APPOINTMENT MANAGEMENT
# =========================================================

app.include_router(
    appointments_router,
    prefix=settings.API_V1_PREFIX,
)

app.include_router(
    doctor_availability_router,
    prefix=settings.API_V1_PREFIX,
)


# =========================================================
# COMPATIBILITY / LEGACY API
# =========================================================

app.include_router(
    api_router,
    prefix="/api",
    include_in_schema=False,
)

app.include_router(
    health_router,
    include_in_schema=False,
)


# =========================================================
# PATIENT PORTAL COMPATIBILITY ROUTES
# =========================================================

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


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root() -> dict:
    return {
        "success": True,
        "message": (
            "Welcome to Sri Sri Wellbeing API"
        ),
    }