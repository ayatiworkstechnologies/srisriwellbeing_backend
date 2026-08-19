from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


# ============================================================
# CONSULTATION
# ============================================================

class Consultation(BaseModel):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "appointments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    duty_doctor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="IN_PROGRESS",
        index=True,
    )

    chief_complaint: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    medical_assessment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    clinical_observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    follow_up_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "appointment_id",
            name="uq_consultations_appointment_id",
        ),
        Index(
            "ix_consultations_patient_status",
            "patient_id",
            "status",
        ),
        Index(
            "ix_consultations_doctor_status",
            "duty_doctor_id",
            "status",
        ),
    )


# ============================================================
# PATIENT VITALS
# ============================================================

class PatientVital(BaseModel):
    __tablename__ = "patient_vitals"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    recorded_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    temperature: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )

    systolic_bp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    diastolic_bp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    pulse_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    respiratory_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    oxygen_saturation: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    weight_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    bmi: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


# ============================================================
# DIAGNOSIS
# ============================================================

class Diagnosis(BaseModel):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    diagnosed_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    diagnosis_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    diagnosis_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    diagnosis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PROVISIONAL",
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


# ============================================================
# CLINICAL NOTES
# ============================================================

class ClinicalNote(BaseModel):
    __tablename__ = "clinical_notes"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    note_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="INITIAL",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


# ============================================================
# SPECIALIST REFERRALS
# ============================================================

class SpecialistReferral(BaseModel):
    __tablename__ = "specialist_referrals"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    referred_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    specialist_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    specialty: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NORMAL",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    referral_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


# ============================================================
# CASE SHARING
# ============================================================

class CaseShare(BaseModel):
    __tablename__ = "case_shares"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    shared_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    shared_with_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    share_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
        index=True,
    )
