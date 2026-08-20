from datetime import datetime
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# COMMON BASE SCHEMA
# ============================================================


class StrictRequestModel(BaseModel):
    """
    Base model for API request payloads.

    Unknown fields are rejected instead of silently ignored.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# ============================================================
# ROLE / PERMISSION RESPONSES
# ============================================================


class RoleResponse(BaseModel):
    id: int | None = None
    name: str


class PermissionResponse(BaseModel):
    id: int | None = None
    code: str
    name: str | None = None


# ============================================================
# USER PROFILE RESPONSES
# ============================================================


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    status: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AuthenticatedUserResponse(UserProfileResponse):
    roles: list[str] = Field(
        default_factory=list,
    )

    permissions: list[str] = Field(
        default_factory=list,
    )


# ============================================================
# PROFILE UPDATE
# ============================================================


class UserProfileUpdateRequest(StrictRequestModel):
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

        normalized_value = " ".join(
            value.strip().split()
        )

        if len(normalized_value) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters"
            )

        return normalized_value

    @field_validator("phone")
    @classmethod
    def normalize_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return validate_and_normalize_phone(value)


# ============================================================
# ACCOUNT STATUS
# ============================================================


class AccountStatusUpdateRequest(StrictRequestModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = " ".join(
            value.strip().split()
        )

        if not normalized:
            return None

        return normalized


# ============================================================
# STAFF REGISTRATION
# ============================================================


class RegisterRequest(StrictRequestModel):
    """
    Staff account creation request.

    IMPORTANT:
    This schema contains role_id because /auth/register must
    be protected by the `users.manage` permission.

    Public patient registration must use a separate
    patient registration schema and must NOT accept role_id.
    """

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

    role_id: int = Field(
        gt=0,
        description=(
            "Active staff role to assign to the new user. "
            "The endpoint must require users.manage."
        ),
    )

    @field_validator("full_name")
    @classmethod
    def clean_full_name(
        cls,
        value: str,
    ) -> str:
        cleaned_value = " ".join(
            value.strip().split()
        )

        if len(cleaned_value) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters"
            )

        return cleaned_value

    @field_validator("email")
    @classmethod
    def clean_email(
        cls,
        value: EmailStr,
    ) -> str:
        return str(value).lower().strip()

    @field_validator("phone")
    @classmethod
    def clean_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return validate_and_normalize_phone(value)

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        validate_password_strength(value)
        return value

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError(
                "Password and confirm password do not match"
            )

        return self


# ============================================================
# LOGIN
# ============================================================


class LoginRequest(StrictRequestModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Optional assigned role for this session. "
            "The first active assigned role is used "
            "when omitted."
        ),
    )

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr,
    ) -> str:
        return str(value).lower().strip()


# ============================================================
# REFRESH TOKEN
# ============================================================


class RefreshTokenRequest(StrictRequestModel):
    refresh_token: str = Field(
        min_length=20,
        max_length=4096,
    )

    @field_validator("refresh_token")
    @classmethod
    def normalize_refresh_token(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Refresh token cannot be empty"
            )

        return value


# ============================================================
# TOKEN RESPONSE
# ============================================================


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        gt=0,
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================


class ForgotPasswordRequest(StrictRequestModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr,
    ) -> str:
        return str(value).lower().strip()


# ============================================================
# RESET PASSWORD
# ============================================================


class ResetPasswordRequest(StrictRequestModel):
    token: str = Field(
        min_length=20,
        max_length=4096,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("token")
    @classmethod
    def normalize_token(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Reset token cannot be empty"
            )

        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password(
        cls,
        value: str,
    ) -> str:
        validate_password_strength(value)
        return value

    @model_validator(mode="after")
    def validate_passwords(self):
        if (
            self.new_password
            != self.confirm_new_password
        ):
            raise ValueError(
                "New password and confirm password "
                "do not match"
            )

        return self


# ============================================================
# CHANGE PASSWORD
# ============================================================


class ChangePasswordRequest(StrictRequestModel):
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

    @field_validator("new_password")
    @classmethod
    def validate_new_password(
        cls,
        value: str,
    ) -> str:
        validate_password_strength(value)
        return value

    @model_validator(mode="after")
    def validate_passwords(self):
        if (
            self.new_password
            != self.confirm_new_password
        ):
            raise ValueError(
                "New password and confirm password "
                "do not match"
            )

        if (
            self.current_password
            == self.new_password
        ):
            raise ValueError(
                "New password must be different "
                "from current password"
            )

        return self


# ============================================================
# VALIDATION HELPERS
# ============================================================


def validate_and_normalize_phone(
    value: str,
) -> str:
    """
    Normalize a phone number while preserving an optional
    leading + character.
    """

    cleaned_phone = (
        value.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if cleaned_phone.startswith("+"):
        number_part = cleaned_phone[1:]
    else:
        number_part = cleaned_phone

    if not number_part:
        raise ValueError(
            "Phone number cannot be empty"
        )

    if not number_part.isdigit():
        raise ValueError(
            "Phone number must contain only digits"
        )

    if len(number_part) < 10:
        raise ValueError(
            "Phone number must contain at least 10 digits"
        )

    if len(number_part) > 15:
        raise ValueError(
            "Phone number cannot contain more than 15 digits"
        )

    return cleaned_phone


def validate_password_strength(
    value: str,
) -> None:
    """
    Basic password policy.

    Requires:
    - minimum length is already enforced by Field
    - uppercase letter
    - lowercase letter
    - number
    - special character
    """

    if value != value.strip():
        raise ValueError(
            "Password cannot start or end with spaces"
        )

    if not re.search(r"[A-Z]", value):
        raise ValueError(
            "Password must contain at least one "
            "uppercase letter"
        )

    if not re.search(r"[a-z]", value):
        raise ValueError(
            "Password must contain at least one "
            "lowercase letter"
        )

    if not re.search(r"\d", value):
        raise ValueError(
            "Password must contain at least one number"
        )

    if not re.search(
        r"""[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`]""",
        value,
    ):
        raise ValueError(
            "Password must contain at least one "
            "special character"
        )
