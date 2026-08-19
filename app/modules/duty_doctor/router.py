from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.rbac.dependencies import (
    require_permission,
)
from app.modules.users.model import User

from app.modules.duty_doctor.repository import (
    DutyDoctorRepository,
)
from app.modules.duty_doctor.schemas import (
    CaseShareCreate,
    CaseShareResponse,
    ClinicalNoteCreate,
    ClinicalNoteResponse,
    ConsultationCreate,
    ConsultationResponse,
    ConsultationStatusUpdate,
    ConsultationUpdate,
    DiagnosisCreate,
    DiagnosisResponse,
    SpecialistReferralCreate,
    SpecialistReferralResponse,
    VitalCreate,
    VitalResponse,
)
from app.modules.duty_doctor.service import (
    DutyDoctorService,
)


router = APIRouter(
    prefix="/duty-doctor",
    tags=["Duty Doctor Consultation"],
)


# ============================================================
# START CONSULTATION
# ============================================================

@router.post(
    "/consultations",
    response_model=ConsultationResponse,
)
async def create_consultation(
    data: ConsultationCreate,
    current_user: User = Depends(
        require_permission(
            "consultations.create"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await DutyDoctorService.create_consultation(
        db=db,
        doctor_id=current_user.id,
        data=data,
    )


# ============================================================
# MY CONSULTATIONS
# ============================================================

@router.get(
    "/consultations/my",
    response_model=list[ConsultationResponse],
)
async def my_consultations(
    current_user: User = Depends(
        require_permission(
            "consultations.view_own"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return (
        await DutyDoctorRepository.get_my_consultations(
            db=db,
            doctor_id=current_user.id,
        )
    )


# ============================================================
# CONSULTATION DETAILS
# ============================================================

@router.get(
    "/consultations/{consultation_id}",
    response_model=ConsultationResponse,
)
async def get_consultation(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "consultations.view_own"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )


# ============================================================
# UPDATE CONSULTATION
# ============================================================

@router.patch(
    "/consultations/{consultation_id}",
    response_model=ConsultationResponse,
)
async def update_consultation(
    consultation_id: int,
    data: ConsultationUpdate,
    current_user: User = Depends(
        require_permission(
            "consultations.update"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.update_consultation(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


# ============================================================
# UPDATE CONSULTATION STATUS
# ============================================================

@router.patch(
    "/consultations/{consultation_id}/status",
    response_model=ConsultationResponse,
)
async def update_consultation_status(
    consultation_id: int,
    data: ConsultationStatusUpdate,
    current_user: User = Depends(
        require_permission(
            "consultations.status"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.update_status(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        new_status=data.status,
    )


# ============================================================
# VITALS
# ============================================================

@router.post(
    "/consultations/{consultation_id}/vitals",
    response_model=VitalResponse,
)
async def add_vitals(
    consultation_id: int,
    data: VitalCreate,
    current_user: User = Depends(
        require_permission(
            "patient_vitals.manage"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.add_vitals(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


@router.get(
    "/consultations/{consultation_id}/vitals",
    response_model=list[VitalResponse],
)
async def get_vitals(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "patient_vitals.view"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    await DutyDoctorService.require_own_consultation(
        db=db,
        consultation_id=consultation_id,
        doctor_id=current_user.id,
    )

    return await DutyDoctorRepository.get_vitals(
        db=db,
        consultation_id=consultation_id,
    )


# ============================================================
# CLINICAL NOTES
# ============================================================

@router.post(
    "/consultations/{consultation_id}/notes",
    response_model=ClinicalNoteResponse,
)
async def add_note(
    consultation_id: int,
    data: ClinicalNoteCreate,
    current_user: User = Depends(
        require_permission(
            "clinical_notes.manage"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.add_note(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


@router.get(
    "/consultations/{consultation_id}/notes",
    response_model=list[ClinicalNoteResponse],
)
async def get_notes(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "clinical_notes.view"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    await DutyDoctorService.require_own_consultation(
        db=db,
        consultation_id=consultation_id,
        doctor_id=current_user.id,
    )

    return await DutyDoctorRepository.get_notes(
        db=db,
        consultation_id=consultation_id,
    )


# ============================================================
# DIAGNOSIS
# ============================================================

@router.post(
    "/consultations/{consultation_id}/diagnoses",
    response_model=DiagnosisResponse,
)
async def add_diagnosis(
    consultation_id: int,
    data: DiagnosisCreate,
    current_user: User = Depends(
        require_permission(
            "diagnoses.manage"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.add_diagnosis(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


@router.get(
    "/consultations/{consultation_id}/diagnoses",
    response_model=list[DiagnosisResponse],
)
async def get_diagnoses(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "diagnoses.view"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    await DutyDoctorService.require_own_consultation(
        db=db,
        consultation_id=consultation_id,
        doctor_id=current_user.id,
    )

    return await DutyDoctorRepository.get_diagnoses(
        db=db,
        consultation_id=consultation_id,
    )


# ============================================================
# SPECIALIST REFERRAL
# ============================================================

@router.post(
    "/consultations/{consultation_id}/referrals",
    response_model=SpecialistReferralResponse,
)
async def create_referral(
    consultation_id: int,
    data: SpecialistReferralCreate,
    current_user: User = Depends(
        require_permission(
            "specialist_referrals.manage"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.add_referral(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


@router.get(
    "/consultations/{consultation_id}/referrals",
    response_model=list[
        SpecialistReferralResponse
    ],
)
async def get_referrals(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "specialist_referrals.view"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    await DutyDoctorService.require_own_consultation(
        db=db,
        consultation_id=consultation_id,
        doctor_id=current_user.id,
    )

    return await DutyDoctorRepository.get_referrals(
        db=db,
        consultation_id=consultation_id,
    )


# ============================================================
# CASE SHARING
# ============================================================

@router.post(
    "/consultations/{consultation_id}/case-shares",
    response_model=CaseShareResponse,
)
async def share_case(
    consultation_id: int,
    data: CaseShareCreate,
    current_user: User = Depends(
        require_permission(
            "case_shares.manage"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    consultation = (
        await DutyDoctorService.require_own_consultation(
            db=db,
            consultation_id=consultation_id,
            doctor_id=current_user.id,
        )
    )

    return await DutyDoctorService.share_case(
        db=db,
        consultation=consultation,
        doctor_id=current_user.id,
        data=data,
    )


@router.get(
    "/consultations/{consultation_id}/case-shares",
    response_model=list[CaseShareResponse],
)
async def get_case_shares(
    consultation_id: int,
    current_user: User = Depends(
        require_permission(
            "case_shares.view"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    await DutyDoctorService.require_own_consultation(
        db=db,
        consultation_id=consultation_id,
        doctor_id=current_user.id,
    )

    return await DutyDoctorRepository.get_case_shares(
        db=db,
        consultation_id=consultation_id,
    )


# ============================================================
# PATIENT CONSULTATION HISTORY
# ============================================================

@router.get(
    "/patients/{patient_id}/history",
    response_model=list[ConsultationResponse],
)
async def patient_consultation_history(
    patient_id: int,
    current_user: User = Depends(
        require_permission(
            "consultations.history"
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await DutyDoctorRepository.patient_history(
        db=db,
        patient_id=patient_id,
    )
