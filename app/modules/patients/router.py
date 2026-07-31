from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.patients.constants import PatientStatus
from app.modules.patients.schemas import (
    PatientCreate,
    PatientCreateResponse,
    PatientDeleteResponse,
    PatientDuplicateCheckRequest,
    PatientDuplicateCheckResponse,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.modules.patients.service import PatientService


router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


# 1. Create patient
@router.post(
    "",
    response_model=PatientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="1. Create Patient",
)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.create_patient(
        db=db,
        payload=payload,
        created_by=current_user.id,
    )


# 2. List patients
@router.get(
    "",
    response_model=PatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="2. List Patients",
)
async def list_patients(
    search: Optional[str] = Query(
        default=None,
        max_length=255,
    ),
    patient_status: Optional[PatientStatus] = Query(
        default=None,
        alias="status",
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.list_patients(
        db=db,
        search=search,
        patient_status=(
            patient_status.value
            if patient_status is not None
            else None
        ),
        skip=skip,
        limit=limit,
    )


# 3. Get one patient
@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="3. Get Patient",
)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.get_patient(
        db=db,
        patient_id=patient_id,
    )


# 4. Update patient
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="4. Update Patient",
)
async def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.update_patient(
        db=db,
        patient_id=patient_id,
        payload=payload,
        updated_by=current_user.id,
    )


# 5. Duplicate check
@router.post(
    "/duplicate-check",
    response_model=PatientDuplicateCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="6. Check Duplicate Patient",
)
async def check_patient_duplicates(
    payload: PatientDuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.check_duplicates(
        db=db,
        payload=payload,
    )

@router.delete(
    "/{patient_id}",
    response_model=PatientDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="5. Delete Patient",
)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await PatientService.delete_patient(
        db=db,
        patient_id=patient_id,
    )