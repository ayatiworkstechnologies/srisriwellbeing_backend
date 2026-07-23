from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    def normalize_name(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")


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


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    description: str | None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PermissionCreateRequest(BaseModel):
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

    @field_validator("module", "action")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")


class PermissionUpdateRequest(BaseModel):
    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    action: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[int] = Field(
        default_factory=list,
        description="Permission IDs to assign to the role",
    )


class AssignRolesRequest(BaseModel):
    role_ids: list[int] = Field(
        default_factory=list,
        description="Role IDs to assign to the user",
    )