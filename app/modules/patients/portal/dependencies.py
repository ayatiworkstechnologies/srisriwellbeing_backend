from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.patients.models import Patient
from app.modules.patients.portal.auth_service import (
    PatientPortalAuthService,
)
from app.modules.patients.portal.repository import (
    PatientPortalRepository,
)
from app.modules.rbac.dependencies import (
    require_role,
)
from app.modules.users.model import User


patient_role_dependency = require_role(
    "patient"
)


CurrentPatientUser = Annotated[
    User,
    Depends(patient_role_dependency),
]


async def get_current_patient(
    current_user: CurrentPatientUser,
    db: AsyncSession = Depends(get_db),
) -> Patient:
    patient = (
        await PatientPortalRepository
        .get_patient_by_user_id(
            db=db,
            user_id=current_user.id,
        )
    )

    if patient is None:
        patient = await (
            PatientPortalAuthService.ensure_patient_profile(
                db=db,
                user=current_user,
            )
        )

    return patient


CurrentPatient = Annotated[
    Patient,
    Depends(get_current_patient),
]
