from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CONSULTATION
# ============================================================

class ConsultationCreate(BaseModel):
    patient_id: int
    appointment_id: int | None = None

    chief_complaint: str | None = None


class ConsultationUpdate(BaseModel):
    chief_complaint: str | None = None
    medical_assessment: str | None = None
    clinical_observations: str | None = None
    follow_up_instructions: str | None = None


class ConsultationStatusUpdate(BaseModel):
    status: Literal[
        "IN_PROGRESS",
        "REFERRED",
        "COMPLETED",
        "CANCELLED",
    ]


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    appointment_id: int | None
    duty_doctor_id: int
    status: str

    chief_complaint: str | None
    medical_assessment: str | None
    clinical_observations: str | None
    follow_up_instructions: str | None


# ============================================================
# VITALS
# ============================================================

class VitalCreate(BaseModel):
    temperature: Decimal | None = None

    systolic_bp: int | None = Field(
        default=None,
        ge=40,
        le=300,
    )

    diastolic_bp: int | None = Field(
        default=None,
        ge=20,
        le=200,
    )

    pulse_rate: int | None = Field(
        default=None,
        ge=20,
        le=250,
    )

    respiratory_rate: int | None = Field(
        default=None,
        ge=5,
        le=80,
    )

    oxygen_saturation: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None

    notes: str | None = None


class VitalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    patient_id: int
    recorded_by: int

    temperature: Decimal | None

    systolic_bp: int | None
    diastolic_bp: int | None
    pulse_rate: int | None
    respiratory_rate: int | None

    oxygen_saturation: Decimal | None

    height_cm: Decimal | None
    weight_kg: Decimal | None
    bmi: Decimal | None

    notes: str | None


# ============================================================
# CLINICAL NOTES
# ============================================================

class ClinicalNoteCreate(BaseModel):
    note_type: Literal[
        "INITIAL",
        "ASSESSMENT",
        "OBSERVATION",
        "FOLLOW_UP",
    ] = "INITIAL"

    content: str = Field(
        min_length=1,
    )


class ClinicalNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    patient_id: int
    doctor_id: int
    note_type: str
    content: str


# ============================================================
# DIAGNOSIS
# ============================================================

class DiagnosisCreate(BaseModel):
    diagnosis_code: str | None = None

    diagnosis_name: str = Field(
        min_length=1,
        max_length=255,
    )

    diagnosis_type: Literal[
        "PROVISIONAL",
        "FINAL",
        "DIFFERENTIAL",
    ] = "PROVISIONAL"

    is_primary: bool = False

    notes: str | None = None


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    patient_id: int
    diagnosed_by: int

    diagnosis_code: str | None
    diagnosis_name: str
    diagnosis_type: str
    is_primary: bool

    notes: str | None


# ============================================================
# SPECIALIST REFERRAL
# ============================================================

class SpecialistReferralCreate(BaseModel):
    specialist_id: int | None = None

    specialty: str | None = None

    reason: str

    priority: Literal[
        "LOW",
        "NORMAL",
        "HIGH",
        "URGENT",
    ] = "NORMAL"

    referral_notes: str | None = None


class ReferralStatusUpdate(BaseModel):
    status: Literal[
        "PENDING",
        "ACCEPTED",
        "REJECTED",
        "COMPLETED",
        "CANCELLED",
    ]


class SpecialistReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    patient_id: int
    referred_by: int

    specialist_id: int | None
    specialty: str | None
    reason: str
    priority: str
    status: str

    referral_notes: str | None


# ============================================================
# CASE SHARE
# ============================================================

class CaseShareCreate(BaseModel):
    shared_with_user_id: int

    share_note: str | None = None


class CaseShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultation_id: int
    patient_id: int

    shared_by: int
    shared_with_user_id: int

    share_note: str | None

    status: str
