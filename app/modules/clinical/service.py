from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit_logs.service import AuditLogService
from app.modules.clinical.models import (
    ConsentTemplate,
    PatientAllergy,
    PatientCondition,
    PatientConsent,
    PatientEmergencyContact,
    PatientExistingMedicine,
    PatientMedicalHistory,
    PatientSurgery,
)
from app.modules.patients.models import Patient

RESOURCE_MODELS = {
    "conditions": PatientCondition,
    "surgeries": PatientSurgery,
    "medicines": PatientExistingMedicine,
    "allergies": PatientAllergy,
    "emergency-contacts": PatientEmergencyContact,
    "consents": PatientConsent,
}

EDITABLE_FIELDS = {
    "conditions": {"name", "diagnosed_on", "status", "notes"},
    "surgeries": {"procedure_name", "surgery_date", "facility", "notes"},
    "medicines": {
        "medicine_name",
        "dosage",
        "frequency",
        "started_on",
        "is_active",
        "notes",
    },
    "allergies": {
        "allergy_type",
        "allergen",
        "severity",
        "reaction",
        "is_active",
    },
    "emergency-contacts": {
        "full_name",
        "relationship",
        "phone",
        "email",
        "is_primary",
    },
    "consents": {"signer_name", "signature_data", "document_path"},
}


def serialize_model(instance) -> dict[str, Any]:
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }


class ClinicalService:
    @staticmethod
    async def require_patient(db: AsyncSession, patient_id: int) -> None:
        patient = await db.get(Patient, patient_id)
        if patient is None:
            raise HTTPException(status_code=404, detail="Patient not found")

    @staticmethod
    async def upsert_history(
        db: AsyncSession,
        patient_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        await ClinicalService.require_patient(db, patient_id)
        result = await db.execute(
            select(PatientMedicalHistory).where(
                PatientMedicalHistory.patient_id == patient_id,
                PatientMedicalHistory.is_deleted.is_(False),
            )
        )
        history = result.scalar_one_or_none()
        if history is None:
            history = PatientMedicalHistory(
                patient_id=patient_id,
                recorded_by=user_id,
                **data,
            )
            db.add(history)
        else:
            for field, value in data.items():
                setattr(history, field, value)
            history.recorded_by = user_id
        await db.flush()
        await AuditLogService.record(
            db,
            user_id=user_id,
            action="UPSERT",
            module="medical_history",
            entity_type="PatientMedicalHistory",
            entity_id=history.id,
            new_values=data,
        )
        await db.commit()
        await db.refresh(history)
        return {
            "success": True,
            "message": "Medical history saved",
            "data": serialize_model(history),
        }

    @staticmethod
    async def create_resource(
        db: AsyncSession,
        patient_id: int,
        resource: str,
        data: dict,
        user_id: int,
    ) -> dict:
        await ClinicalService.require_patient(db, patient_id)
        model = RESOURCE_MODELS[resource]
        if resource == "consents":
            template = await db.get(
                ConsentTemplate, data["consent_template_id"]
            )
            if template is None or not template.is_active:
                raise HTTPException(
                    status_code=404, detail="Active consent template not found"
                )
            data["captured_by"] = user_id
        elif hasattr(model, "recorded_by"):
            data["recorded_by"] = user_id
        item = model(patient_id=patient_id, **data)
        db.add(item)
        await db.flush()
        await AuditLogService.record(
            db,
            user_id=user_id,
            action="CREATE",
            module="clinical_record",
            entity_type=model.__name__,
            entity_id=item.id,
            new_values=data,
        )
        await db.commit()
        await db.refresh(item)
        return {
            "success": True,
            "message": f"{resource} record created",
            "data": serialize_model(item),
        }

    @staticmethod
    async def list_resource(
        db: AsyncSession,
        patient_id: int,
        resource: str,
    ) -> dict:
        await ClinicalService.require_patient(db, patient_id)
        model = RESOURCE_MODELS[resource]
        result = await db.execute(
            select(model)
            .where(
                model.patient_id == patient_id,
                model.is_deleted.is_(False),
            )
            .order_by(model.id.desc())
        )
        items = result.scalars().all()
        return {
            "success": True,
            "message": f"{resource} retrieved",
            "data": [serialize_model(item) for item in items],
        }

    @staticmethod
    async def delete_resource(
        db: AsyncSession,
        patient_id: int,
        resource: str,
        item_id: int,
        user_id: int,
    ) -> dict:
        model = RESOURCE_MODELS[resource]
        item = await db.get(model, item_id)
        if item is None or item.patient_id != patient_id or item.is_deleted:
            raise HTTPException(
                status_code=404, detail="Clinical record not found"
            )
        item.is_deleted = True
        await AuditLogService.record(
            db,
            user_id=user_id,
            action="DELETE",
            module="clinical_record",
            entity_type=model.__name__,
            entity_id=item.id,
        )
        await db.commit()
        return {"success": True, "message": "Clinical record deleted"}

    @staticmethod
    async def update_resource(
        db: AsyncSession,
        patient_id: int,
        resource: str,
        item_id: int,
        data: dict,
        user_id: int,
    ) -> dict:
        model = RESOURCE_MODELS[resource]
        item = await db.get(model, item_id)
        if item is None or item.patient_id != patient_id or item.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="Clinical record not found",
            )
        changes = {
            key: value
            for key, value in data.items()
            if key in EDITABLE_FIELDS[resource] and value is not None
        }
        if not changes:
            raise HTTPException(
                status_code=422, detail="No editable fields provided"
            )
        for field, value in changes.items():
            if hasattr(item, field):
                setattr(item, field, value)
        await AuditLogService.record(
            db,
            user_id=user_id,
            action="UPDATE",
            module="clinical_record",
            entity_type=model.__name__,
            entity_id=item.id,
            new_values=changes,
        )
        await db.commit()
        await db.refresh(item)
        return {
            "success": True,
            "message": "Clinical record updated",
            "data": serialize_model(item),
        }

    @staticmethod
    async def create_template(db: AsyncSession, data: dict) -> dict:
        template = ConsentTemplate(**data)
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return {
            "success": True,
            "message": "Consent template created",
            "data": serialize_model(template),
        }

    @staticmethod
    async def list_templates(db: AsyncSession) -> dict:
        result = await db.execute(
            select(ConsentTemplate).where(
                ConsentTemplate.is_deleted.is_(False)
            )
        )
        return {
            "success": True,
            "message": "Consent templates retrieved",
            "data": [serialize_model(item) for item in result.scalars().all()],
        }

    @staticmethod
    async def revoke_consent(
        db: AsyncSession, patient_id: int, consent_id: int
    ) -> dict:
        consent = await db.get(PatientConsent, consent_id)
        if (
            consent is None
            or consent.patient_id != patient_id
            or consent.is_deleted
        ):
            raise HTTPException(status_code=404, detail="Consent not found")
        consent.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        return {"success": True, "message": "Consent revoked"}

    @staticmethod
    async def clinical_summary(db: AsyncSession, patient_id: int) -> dict:
        await ClinicalService.require_patient(db, patient_id)
        summary = {}
        for resource in RESOURCE_MODELS:
            summary[resource.replace("-", "_")] = (
                await ClinicalService.list_resource(db, patient_id, resource)
            )["data"]
        history_result = await db.execute(
            select(PatientMedicalHistory).where(
                PatientMedicalHistory.patient_id == patient_id,
                PatientMedicalHistory.is_deleted.is_(False),
            )
        )
        history = history_result.scalar_one_or_none()
        summary["medical_history"] = (
            serialize_model(history) if history else None
        )
        summary["allergy_alerts"] = [
            allergy for allergy in summary["allergies"] if allergy["is_active"]
        ]
        summary["inpatient_admission_ready"] = bool(
            summary["emergency_contacts"]
        )
        return {
            "success": True,
            "message": "Clinical record retrieved",
            "data": summary,
        }

    @staticmethod
    async def validate_admission_readiness(
        db: AsyncSession,
        patient_id: int,
    ) -> dict:
        summary = (await ClinicalService.clinical_summary(db, patient_id))[
            "data"
        ]
        if not summary["emergency_contacts"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": (
                        "At least one emergency contact is required for "
                        "in-patient admission"
                    ),
                    "missing": ["emergency_contact"],
                },
            )
        return {
            "success": True,
            "message": "Patient is ready for in-patient admission",
            "data": {
                "patient_id": patient_id,
                "allergy_alerts": summary["allergy_alerts"],
            },
        }
