from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.duty_doctor.audit import (
    create_clinical_audit,
)
from app.modules.duty_doctor.model import (
    CaseShare,
    ClinicalNote,
    Consultation,
    Diagnosis,
    PatientVital,
    SpecialistReferral,
)
from app.modules.duty_doctor.repository import (
    DutyDoctorRepository,
)
from app.modules.duty_doctor.schemas import (
    CaseShareCreate,
    ClinicalNoteCreate,
    ConsultationCreate,
    ConsultationUpdate,
    DiagnosisCreate,
    SpecialistReferralCreate,
    VitalCreate,
)


class DutyDoctorService:

    @staticmethod
    async def require_own_consultation(
        db: AsyncSession,
        consultation_id: int,
        doctor_id: int,
    ) -> Consultation:

        consultation = (
            await DutyDoctorRepository.get_doctor_consultation(
                db=db,
                consultation_id=consultation_id,
                doctor_id=doctor_id,
            )
        )

        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )

        return consultation

    @staticmethod
    async def create_consultation(
        db: AsyncSession,
        doctor_id: int,
        data: ConsultationCreate,
    ) -> Consultation:

        consultation = Consultation(
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            duty_doctor_id=doctor_id,
            status="IN_PROGRESS",
            chief_complaint=data.chief_complaint,
        )

        db.add(consultation)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="consultation",
            entity_id=consultation.id,
            description="Duty doctor started consultation",
            new_values={
                "patient_id": data.patient_id,
                "appointment_id": data.appointment_id,
                "status": "IN_PROGRESS",
            },
        )

        await db.commit()
        await db.refresh(consultation)

        return consultation

    @staticmethod
    async def update_consultation(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: ConsultationUpdate,
    ) -> Consultation:

        old_values = {
            "chief_complaint":
                consultation.chief_complaint,
            "medical_assessment":
                consultation.medical_assessment,
            "clinical_observations":
                consultation.clinical_observations,
            "follow_up_instructions":
                consultation.follow_up_instructions,
        }

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(
                consultation,
                key,
                value,
            )

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="UPDATE",
            entity_type="consultation",
            entity_id=consultation.id,
            description="Clinical consultation updated",
            old_values=old_values,
            new_values=update_data,
        )

        await db.commit()
        await db.refresh(consultation)

        return consultation

    @staticmethod
    async def add_vitals(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: VitalCreate,
    ) -> PatientVital:

        bmi = None

        if (
            data.height_cm
            and data.weight_kg
            and data.height_cm > 0
        ):
            height_m = (
                Decimal(data.height_cm)
                / Decimal("100")
            )

            bmi = (
                Decimal(data.weight_kg)
                / (height_m * height_m)
            ).quantize(
                Decimal("0.01")
            )

        vital = PatientVital(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            recorded_by=doctor_id,
            temperature=data.temperature,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            pulse_rate=data.pulse_rate,
            respiratory_rate=data.respiratory_rate,
            oxygen_saturation=data.oxygen_saturation,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            bmi=bmi,
            notes=data.notes,
        )

        db.add(vital)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="patient_vital",
            entity_id=vital.id,
            description="Patient vital signs recorded",
            new_values=data.model_dump(
                mode="json"
            ),
        )

        await db.commit()
        await db.refresh(vital)

        return vital

    @staticmethod
    async def add_note(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: ClinicalNoteCreate,
    ) -> ClinicalNote:

        note = ClinicalNote(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            doctor_id=doctor_id,
            note_type=data.note_type,
            content=data.content,
        )

        db.add(note)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="clinical_note",
            entity_id=note.id,
            description=(
                f"{data.note_type} clinical note added"
            ),
            new_values={
                "note_type": data.note_type,
            },
        )

        await db.commit()
        await db.refresh(note)

        return note

    @staticmethod
    async def add_diagnosis(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: DiagnosisCreate,
    ) -> Diagnosis:

        diagnosis = Diagnosis(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            diagnosed_by=doctor_id,
            diagnosis_code=data.diagnosis_code,
            diagnosis_name=data.diagnosis_name,
            diagnosis_type=data.diagnosis_type,
            is_primary=data.is_primary,
            notes=data.notes,
        )

        db.add(diagnosis)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="diagnosis",
            entity_id=diagnosis.id,
            description="Patient diagnosis recorded",
            new_values=data.model_dump(
                mode="json"
            ),
        )

        await db.commit()
        await db.refresh(diagnosis)

        return diagnosis

    @staticmethod
    async def add_referral(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: SpecialistReferralCreate,
    ) -> SpecialistReferral:

        referral = SpecialistReferral(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            referred_by=doctor_id,
            specialist_id=data.specialist_id,
            specialty=data.specialty,
            reason=data.reason,
            priority=data.priority,
            referral_notes=data.referral_notes,
            status="PENDING",
        )

        consultation.status = "REFERRED"

        db.add(referral)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="specialist_referral",
            entity_id=referral.id,
            description="Patient referred to specialist",
            new_values=data.model_dump(
                mode="json"
            ),
        )

        await db.commit()
        await db.refresh(referral)

        return referral

    @staticmethod
    async def share_case(
        db: AsyncSession,
        consultation: Consultation,
        doctor_id: int,
        data: CaseShareCreate,
    ) -> CaseShare:

        if (
            data.shared_with_user_id
            == doctor_id
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot share a case "
                    "with yourself"
                ),
            )

        case_share = CaseShare(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            shared_by=doctor_id,
            shared_with_user_id=(
                data.shared_with_user_id
            ),
            share_note=data.share_note,
            status="ACTIVE",
        )

        db.add(case_share)

        await db.flush()

        await create_clinical_audit(
            db=db,
            user_id=doctor_id,
            action="CREATE",
            entity_type="case_share",
            entity_id=case_share.id,
            description="Clinical case shared",
            new_values={
                "shared_with_user_id":
                    data.shared_with_user_id,
            },
        )

        await db.commit()
        await db.refresh(case_share)

        return case_share
