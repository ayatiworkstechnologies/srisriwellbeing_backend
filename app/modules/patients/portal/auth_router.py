from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import CurrentAuthContext
from app.modules.auth.service import AuthService
from app.modules.patients.portal.auth_service import (
    PatientPortalAuthService,
)
from app.modules.patients.portal.schemas import (
    PatientLoginRequest,
    PatientRegisterRequest,
)
from app.modules.users.repository import UserRepository

router = APIRouter()


def get_client_ip(
    request: Request,
) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None


@router.post(
    "/register",
    status_code=201,
)
async def patient_register(
    payload: PatientRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await PatientPortalAuthService.register(
        db=db,
        payload=payload,
    )


@router.post("/login")
async def patient_login(
    payload: PatientLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await AuthService.login(
        db=db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=get_client_ip(request),
        allowed_roles=["patient"],
    )

    user = await UserRepository.get_by_email(
        db=db,
        email=payload.email,
    )
    patient = await PatientPortalAuthService.ensure_patient_profile(
        db=db,
        user=user,
    )

    result["data"]["dashboard"] = "/patient/dashboard"
    result["data"]["patient"] = {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "first_name": patient.first_name,
        "middle_name": patient.middle_name,
        "last_name": patient.last_name,
        "full_name": " ".join(
            name
            for name in (
                patient.first_name,
                patient.middle_name,
                patient.last_name,
            )
            if name
        ),
        "email": patient.email,
        "mobile_number": patient.mobile_number,
        "status": patient.status,
    }

    return result


@router.post("/logout")
async def patient_logout(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.logout(
        db=db,
        session_id=auth_context.session_id,
    )
