from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# =========================================================
# USER ROLE ASSIGNMENT
# =========================================================


class UserRoleAssignRequest(BaseModel):
    role_ids: list[int] = Field(
        ...,
        min_length=1,
        description=(
            "Role IDs to assign to the user"
        ),
    )

    @field_validator("role_ids")
    @classmethod
    def validate_role_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        cleaned_ids = list(
            dict.fromkeys(value)
        )

        if any(
            role_id <= 0
            for role_id in cleaned_ids
        ):
            raise ValueError(
                "Role IDs must be positive integers."
            )

        return cleaned_ids


# Keep this because existing routes may already
# import AssignRolesRequest.
class AssignRolesRequest(
    UserRoleAssignRequest
):
    pass


# =========================================================
# ROLE CREATE
# =========================================================


class RoleCreateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    display_name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        return (
            value
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    @field_validator(
        "display_name"
    )
    @classmethod
    def normalize_display_name(
        cls,
        value: str,
    ) -> str:
        return value.strip()

    @field_validator(
        "description"
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


# =========================================================
# ROLE UPDATE
# =========================================================


class RoleUpdateRequest(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool | None = None

    @field_validator(
        "display_name"
    )
    @classmethod
    def normalize_display_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip()

    @field_validator(
        "description"
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


# =========================================================
# ROLE RESPONSE
# =========================================================


class RoleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    display_name: str
    description: str | None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =========================================================
# USER ROLE RESPONSE
# =========================================================


class UserRoleItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    display_name: str
    is_active: bool


class UserRolesResponse(BaseModel):
    user_id: int

    roles: list[
        UserRoleItemResponse
    ]


# =========================================================
# PERMISSION CREATE
# =========================================================


class PermissionCreateRequest(
    BaseModel
):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    module: str = Field(
        min_length=2,
        max_length=100,
    )

    action: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator(
        "module",
        "action",
    )
    @classmethod
    def normalize_value(
        cls,
        value: str,
    ) -> str:
        return (
            value
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    @field_validator(
        "description"
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator("name")
    @classmethod
    def normalize_permission_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        return value.strip()


# =========================================================
# PERMISSION UPDATE
# =========================================================


class PermissionUpdateRequest(
    BaseModel
):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool | None = None

    @field_validator(
        "description"
    )
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator("name")
    @classmethod
    def normalize_permission_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        return value.strip()


# =========================================================
# PERMISSION RESPONSE
# =========================================================


class PermissionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    name: str
    module: str
    action: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =========================================================
# ASSIGN PERMISSIONS TO ROLE
# =========================================================


class AssignPermissionsRequest(
    BaseModel
):
    permission_ids: list[int] = Field(
        default_factory=list,
        description=(
            "Permission IDs to assign to the role"
        ),
    )

    @field_validator(
        "permission_ids"
    )
    @classmethod
    def validate_permission_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        cleaned_ids = list(
            dict.fromkeys(value)
        )

        if any(
            permission_id <= 0
            for permission_id
            in cleaned_ids
        ):
            raise ValueError(
                "Permission IDs must be positive integers."
            )

        return cleaned_ids
