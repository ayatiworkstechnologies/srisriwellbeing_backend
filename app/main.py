from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.schema_migrations import (
    ensure_patient_portal_schema,
)
from app.models.base import Base
from app import models  # noqa: F401
from app.modules.patients.portal.auth_router import (
    router as patient_auth_router,
)
from app.modules.patients.portal.dashboard_router import (
    router as patient_dashboard_router,
)
from app.modules.users.router import router as users_router
from app.api.endpoints import audit_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await ensure_patient_portal_schema(connection)

    print("Database tables created successfully")

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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    api_router,
    prefix="/api",
)

# Compatibility aliases for frontend deployments whose API URL does not
# include the canonical ``/api`` prefix.
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

app.include_router(users_router)
app.include_router(audit_logs.router)
