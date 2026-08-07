from datetime import date, datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class PatientCreate(BaseModel):
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Arun"],
    )

    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        examples=["9876543210"],
    )

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("First name is required")

        return value

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        value = value.strip()

        if not value.isdigit():
            raise ValueError("Mobile number must contain only numbers")

        if len(value) < 10 or len(value) > 15:
            raise ValueError("Mobile number must contain 10 to 15 digits")

        return value


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    alternate_mobile_number: Optional[str] = None
    email: Optional[str] = None
    presenting_concern: Optional[str] = None


class PatientCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: str
    first_name: str
    mobile_number: str
    status: str
    created_at: datetime


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_code: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: str
    alternate_mobile_number: Optional[str] = None
    email: Optional[str] = None
    presenting_concern: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[PatientResponse]


class PatientDuplicateCheckRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    mobile_number: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
    )
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None

    @field_validator(
        "first_name",
        "middle_name",
        "last_name",
        "mobile_number",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_duplicate_identifier(self):
        if not any(
            (
                self.mobile_number,
                self.email,
                self.date_of_birth,
                self.first_name,
            )
        ):
            raise ValueError(
                "Provide a mobile number, email, date of birth, or first name"
            )
        return self


class DuplicatePatientMatchResponse(BaseModel):
    patient_id: int
    patient_code: str
    full_name: str
    mobile_number: str
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    mobile_match: bool
    email_match: bool
    date_of_birth_match: bool
    name_similarity_score: int
    overall_match_score: int


class PatientDuplicateCheckResponse(BaseModel):
    has_possible_duplicates: bool
    matches: list[DuplicatePatientMatchResponse]
    is_duplicate: bool
    patient_id: Optional[int] = None
    patient_code: Optional[str] = None
    message: str


class PatientDeleteResponse(BaseModel):
    message: str
    patient_id: int
