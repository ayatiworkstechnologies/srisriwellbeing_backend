from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class MedicalHistoryUpsert(BaseModel):
    previous_illnesses: str | None = None
    chronic_conditions: str | None = None
    family_history: str | None = None
    notes: str | None = None


class ConditionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    diagnosed_on: date | None = None
    status: str = Field(default="active", max_length=30)
    notes: str | None = None


class SurgeryCreate(BaseModel):
    procedure_name: str = Field(min_length=2, max_length=200)
    surgery_date: date | None = None
    facility: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class MedicineCreate(BaseModel):
    medicine_name: str = Field(min_length=2, max_length=200)
    dosage: str | None = Field(default=None, max_length=100)
    frequency: str | None = Field(default=None, max_length=100)
    started_on: date | None = None
    is_active: bool = True
    notes: str | None = None


class AllergyCreate(BaseModel):
    allergy_type: Literal["drug", "food", "environmental"]
    allergen: str = Field(min_length=2, max_length=200)
    severity: Literal["mild", "moderate", "severe", "life_threatening"]
    reaction: str | None = None
    is_active: bool = True


class EmergencyContactCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    relationship: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None
    is_primary: bool = False


class ConsentTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    version: str = Field(min_length=1, max_length=30)
    content: str = Field(min_length=10)
    is_active: bool = True


class PatientConsentCreate(BaseModel):
    consent_template_id: int = Field(gt=0)
    signer_name: str = Field(min_length=2, max_length=150)
    signature_data: str | None = None
    document_path: str | None = Field(default=None, max_length=500)
