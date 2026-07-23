from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )
    email: EmailStr
    phone: str | None = Field(
        default=None,
        max_length=20,
    )
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    role_ids: list[int] = Field(
        default_factory=list,
    )


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        max_length=20,
    )
    role_ids: list[int] | None = None


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    status: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None
    roles: list[UserRoleResponse] = Field(
        default_factory=list,
    )

class UserListResponse(BaseModel):
    success: bool
    message: str
    data: list[UserResponse]


class UserDetailResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse