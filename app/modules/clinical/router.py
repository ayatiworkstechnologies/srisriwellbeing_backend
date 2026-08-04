from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.modules.clinical.schemas import (
    AllergyCreate,
    ConditionCreate,
    ConsentTemplateCreate,
    EmergencyContactCreate,
    MedicalHistoryUpsert,
    MedicineCreate,
    PatientConsentCreate,
    SurgeryCreate,
)
from app.modules.clinical.service import ClinicalService

router = APIRouter(prefix="/patients", tags=["Clinical Records"])
CLINICAL_RESOURCE_PATTERN = (
    "^(conditions|surgeries|medicines|allergies|"
    "emergency-contacts|consents)$"
)


@router.get("/{patient_id}/clinical-summary")
async def get_clinical_summary(
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("medical_history.view")),
):
    return await ClinicalService.clinical_summary(db, patient_id)


@router.get("/{patient_id}/admission-readiness")
async def validate_admission_readiness(
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("medical_history.view")),
):
    return await ClinicalService.validate_admission_readiness(db, patient_id)


@router.put("/{patient_id}/medical-history")
async def save_medical_history(
    payload: MedicalHistoryUpsert,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await ClinicalService.upsert_history(
        db, patient_id, payload.model_dump(), user.id
    )


async def _create(db, patient_id, resource, payload, user):
    return await ClinicalService.create_resource(
        db, patient_id, resource, payload.model_dump(), user.id
    )


@router.post("/{patient_id}/conditions", status_code=status.HTTP_201_CREATED)
async def create_condition(
    payload: ConditionCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await _create(db, patient_id, "conditions", payload, user)


@router.post("/{patient_id}/surgeries", status_code=status.HTTP_201_CREATED)
async def create_surgery(
    payload: SurgeryCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await _create(db, patient_id, "surgeries", payload, user)


@router.post("/{patient_id}/medicines", status_code=status.HTTP_201_CREATED)
async def create_medicine(
    payload: MedicineCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await _create(db, patient_id, "medicines", payload, user)


@router.post("/{patient_id}/allergies", status_code=status.HTTP_201_CREATED)
async def create_allergy(
    payload: AllergyCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("allergy.manage")),
):
    return await _create(db, patient_id, "allergies", payload, user)


@router.post("/{patient_id}/emergency-contacts", status_code=201)
async def create_emergency_contact(
    payload: EmergencyContactCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await _create(db, patient_id, "emergency-contacts", payload, user)


@router.post("/{patient_id}/consents", status_code=201)
async def capture_consent(
    payload: PatientConsentCreate,
    patient_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("consent.manage")),
):
    return await _create(db, patient_id, "consents", payload, user)


@router.post("/{patient_id}/consents/{consent_id}/revoke")
async def revoke_consent(
    patient_id: int = Path(gt=0),
    consent_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("consent.manage")),
):
    return await ClinicalService.revoke_consent(db, patient_id, consent_id)


@router.post("/consent-templates", status_code=201)
async def create_consent_template(
    payload: ConsentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("consent.manage")),
):
    return await ClinicalService.create_template(db, payload.model_dump())


@router.get("/consent-templates")
async def list_consent_templates(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("medical_history.view")),
):
    return await ClinicalService.list_templates(db)


@router.get("/{patient_id}/{resource}")
async def list_clinical_resource(
    patient_id: int = Path(gt=0),
    resource: str = Path(pattern=CLINICAL_RESOURCE_PATTERN),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("medical_history.view")),
):
    return await ClinicalService.list_resource(db, patient_id, resource)


@router.delete("/{patient_id}/{resource}/{item_id}")
async def delete_clinical_resource(
    patient_id: int = Path(gt=0),
    resource: str = Path(pattern=CLINICAL_RESOURCE_PATTERN),
    item_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await ClinicalService.delete_resource(
        db, patient_id, resource, item_id, user.id
    )


@router.patch("/{patient_id}/{resource}/{item_id}")
async def update_clinical_resource(
    payload: dict,
    patient_id: int = Path(gt=0),
    resource: str = Path(pattern=CLINICAL_RESOURCE_PATTERN),
    item_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("medical_history.update")),
):
    return await ClinicalService.update_resource(
        db,
        patient_id,
        resource,
        item_id,
        payload,
        user.id,
    )
