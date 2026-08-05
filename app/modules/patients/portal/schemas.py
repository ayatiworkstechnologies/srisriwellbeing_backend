from datetime import date, datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

BloodGroup = Literal[
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
]


class PatientLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class PatientRegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100,
        validation_alias=AliasChoices("full_name", "fullName"),
    )
    email: EmailStr
    phone: str = Field(
        min_length=10,
        max_length=20,
        validation_alias=AliasChoices(
            "phone",
            "mobile_number",
            "mobileNumber",
        ),
    )
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    confirm_password: str = Field(
        min_length=8,
        max_length=128,
        validation_alias=AliasChoices(
            "confirm_password",
            "confirmPassword",
        ),
    )

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("email")
    @classmethod
    def normalize_register_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        cleaned_phone = (
            value.strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        number_part = (
            cleaned_phone[1:]
            if cleaned_phone.startswith("+")
            else cleaned_phone
        )

        if not number_part.isdigit():
            raise ValueError("Phone number must contain only digits")

        if len(number_part) < 10:
            raise ValueError("Phone number must contain at least 10 digits")

        return cleaned_phone

    @model_validator(mode="after")
    def validate_matching_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")

        return self


class PatientAddressData(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    address_type: str

    address_line_1: str
    address_line_2: str | None = None
    landmark: str | None = None

    city: str
    state: str
    country: str
    postal_code: str

    is_primary: bool


class PatientProfileData(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    patient_code: str

    first_name: str
    middle_name: str | None = None
    last_name: str | None = None

    email: EmailStr | None = None

    mobile_number: str
    alternate_mobile_number: str | None = None

    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None

    presenting_concern: str | None = None
    status: str

    addresses: list[PatientAddressData] = Field(
        default_factory=list,
    )

    created_at: datetime
    updated_at: datetime


class PatientProfileResponse(BaseModel):
    success: bool = True
    message: str
    data: PatientProfileData


class PatientProfileUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    email: EmailStr | None = None

    mobile_number: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
    )

    alternate_mobile_number: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
    )

    date_of_birth: date | None = None

    gender: (
        Literal[
            "male",
            "female",
            "other",
        ]
        | None
    ) = None

    blood_group: BloodGroup | None = None

    @field_validator(
        "first_name",
        "middle_name",
        "last_name",
        mode="before",
    )
    @classmethod
    def clean_names(
        cls,
        value,
    ):
        if value is None:
            return None

        cleaned_value = str(value).strip()

        return cleaned_value or None

    @field_validator(
        "mobile_number",
        "alternate_mobile_number",
        mode="before",
    )
    @classmethod
    def clean_mobile_numbers(
        cls,
        value,
    ):
        if value is None:
            return None

        cleaned_value = str(value).strip()

        return cleaned_value or None

    @field_validator(
        "date_of_birth",
    )
    @classmethod
    def validate_date_of_birth(
        cls,
        value: date | None,
    ) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")

        return value


class PatientDashboardPatientData(BaseModel):
    id: int
    patient_code: str

    first_name: str
    middle_name: str | None = None
    last_name: str | None = None

    full_name: str

    email: str | None = None
    mobile_number: str

    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None

    status: str
    created_at: datetime


class PatientDashboardSummary(BaseModel):
    upcoming_appointments: int = 0
    active_prescriptions: int = 0
    new_reports: int = 0
    pending_payments: int = 0


class PatientDashboardData(BaseModel):
    patient: PatientDashboardPatientData
    summary: PatientDashboardSummary


class PatientDashboardResponse(BaseModel):
    success: bool = True
    message: str
    data: PatientDashboardData


class PatientDocumentData(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    patient_id: int

    document_type: str
    title: str

    original_file_name: str
    file_url: str | None = None

    mime_type: str
    file_size: int

    uploaded_by: int | None = None
    created_at: datetime


class PatientDocumentResponse(BaseModel):
    success: bool = True
    message: str
    data: PatientDocumentData


class PatientDocumentListData(BaseModel):
    documents: list[PatientDocumentData] = Field(
        default_factory=list,
    )

    total: int = 0


class PatientDocumentListResponse(BaseModel):
    success: bool = True
    message: str
    data: PatientDocumentListData


class PatientDocumentDeleteResponse(BaseModel):
    success: bool = True
    message: str
    data: dict
