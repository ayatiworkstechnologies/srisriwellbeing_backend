from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class RoleResponse(BaseModel):
    id: int | None = None
    name: str


class PermissionResponse(BaseModel):
    id: int | None = None
    code: str
    name: str | None = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    status: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AuthenticatedUserResponse(UserProfileResponse):
    roles: list[str] = []
    permissions: list[str] = []


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = " ".join(value.strip().split())

        if not normalized_value:
            raise ValueError("Full name cannot be empty")

        return normalized_value

    @field_validator("phone")
    @classmethod
    def normalize_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value


class AccountStatusUpdateRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class RegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        cleaned_value = " ".join(value.strip().split())

        if len(cleaned_value) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters"
            )

        return cleaned_value

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: EmailStr) -> str:
        return str(value).lower().strip()

    @field_validator("phone")
    @classmethod
    def clean_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None or not value.strip():
            return None

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
            raise ValueError(
                "Phone number must contain only digits"
            )

        if len(number_part) < 10:
            raise ValueError(
                "Phone number must contain at least 10 digits"
            )

        return cleaned_phone

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError(
                "Password and confirm password do not match"
            )

        return self


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower().strip()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        min_length=20,
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower().strip()


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=20,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError(
                "New password and confirm password do not match"
            )

        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=8,
        max_length=128,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError(
                "New password and confirm password do not match"
            )

        if self.current_password == self.new_password:
            raise ValueError(
                "New password must be different from current password"
            )

        return self