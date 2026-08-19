from fastapi import APIRouter

from app.api.endpoints.audit_logs import router as audit_logs_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.rbac import router as rbac_router
from app.modules.clinical.router import router as clinical_router
from app.modules.appointments.router import (
    appointments_router,
    doctor_availability_router,
)
from app.modules.patients.portal.auth_router import (
    router as patient_auth_router,
)
from app.modules.patients.portal.dashboard_router import (
    router as patient_dashboard_router,
)
from app.modules.patients.portal.appointments_router import (
    router as patient_appointments_router,
)
from app.modules.patients.router import router as patients_router
from app.modules.users.router import router as users_router

from app.modules.duty_doctor.router import (
    router as duty_doctor_router,
)


api_router = APIRouter()


api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    rbac_router,
    prefix="/rbac",
    tags=["RBAC"],
)

api_router.include_router(users_router)
api_router.include_router(audit_logs_router)
api_router.include_router(clinical_router)
api_router.include_router(appointments_router)
api_router.include_router(doctor_availability_router)
api_router.include_router(duty_doctor_router)
# Include staff-side patient CRUD only once
api_router.include_router(
    patients_router,
    prefix="/patients",
    tags=["Patients"],
)

api_router.include_router(
    patient_auth_router,
    prefix="/patient-auth",
    tags=["Patient Authentication"],
)

api_router.include_router(
    patient_dashboard_router,
    prefix="/patient",
    tags=["Patient Portal"],
)

api_router.include_router(
    patient_appointments_router,
    prefix="/patient",
    tags=["Patient Appointments"],
)
