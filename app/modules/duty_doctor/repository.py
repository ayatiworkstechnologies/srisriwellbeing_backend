from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.duty_doctor.model import (
    CaseShare,
    ClinicalNote,
    Consultation,
    Diagnosis,
    PatientVital,
    SpecialistReferral,
)


class DutyDoctorRepository:

    # ========================================================
    # CONSULTATIONS
    # ========================================================

    @staticmethod
    async def create_consultation(
        db: AsyncSession,
        consultation: Consultation,
    ) -> Consultation:
        db.add(consultation)
        await db.flush()
        await db.refresh(consultation)

        return consultation

    @staticmethod
    async def get_consultation(
        db: AsyncSession,
        consultation_id: int,
    ) -> Consultation | None:

        result = await db.execute(
            select(Consultation).where(
                Consultation.id == consultation_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_doctor_consultation(
        db: AsyncSession,
        consultation_id: int,
        doctor_id: int,
    ) -> Consultation | None:

        result = await db.execute(
            select(Consultation).where(
                Consultation.id == consultation_id,
                Consultation.duty_doctor_id == doctor_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_appointment(
        db: AsyncSession,
        appointment_id: int,
    ) -> Consultation | None:
        result = await db.execute(
            select(Consultation).where(
                Consultation.appointment_id == appointment_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_my_consultations(
        db: AsyncSession,
        doctor_id: int,
    ) -> list[Consultation]:

        result = await db.execute(
            select(Consultation)
            .where(
                Consultation.duty_doctor_id == doctor_id
            )
            .order_by(
                Consultation.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def patient_history(
        db: AsyncSession,
        patient_id: int,
    ) -> list[Consultation]:

        result = await db.execute(
            select(Consultation)
            .where(
                Consultation.patient_id == patient_id
            )
            .order_by(
                Consultation.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # VITALS
    # ========================================================

    @staticmethod
    async def get_vitals(
        db: AsyncSession,
        consultation_id: int,
    ) -> list[PatientVital]:

        result = await db.execute(
            select(PatientVital)
            .where(
                PatientVital.consultation_id
                == consultation_id
            )
            .order_by(
                PatientVital.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # NOTES
    # ========================================================

    @staticmethod
    async def get_notes(
        db: AsyncSession,
        consultation_id: int,
    ) -> list[ClinicalNote]:

        result = await db.execute(
            select(ClinicalNote)
            .where(
                ClinicalNote.consultation_id
                == consultation_id
            )
            .order_by(
                ClinicalNote.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # DIAGNOSIS
    # ========================================================

    @staticmethod
    async def get_diagnoses(
        db: AsyncSession,
        consultation_id: int,
    ) -> list[Diagnosis]:

        result = await db.execute(
            select(Diagnosis)
            .where(
                Diagnosis.consultation_id
                == consultation_id
            )
            .order_by(
                Diagnosis.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # REFERRALS
    # ========================================================

    @staticmethod
    async def get_referrals(
        db: AsyncSession,
        consultation_id: int,
    ) -> list[SpecialistReferral]:

        result = await db.execute(
            select(SpecialistReferral)
            .where(
                SpecialistReferral.consultation_id
                == consultation_id
            )
            .order_by(
                SpecialistReferral.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def get_referral(
        db: AsyncSession,
        consultation_id: int,
        referral_id: int,
    ) -> SpecialistReferral | None:
        result = await db.execute(
            select(SpecialistReferral).where(
                SpecialistReferral.id == referral_id,
                SpecialistReferral.consultation_id
                == consultation_id,
            )
        )

        return result.scalar_one_or_none()

    # ========================================================
    # CASE SHARES
    # ========================================================

    @staticmethod
    async def get_case_shares(
        db: AsyncSession,
        consultation_id: int,
    ) -> list[CaseShare]:

        result = await db.execute(
            select(CaseShare)
            .where(
                CaseShare.consultation_id
                == consultation_id
            )
            .order_by(
                CaseShare.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )
