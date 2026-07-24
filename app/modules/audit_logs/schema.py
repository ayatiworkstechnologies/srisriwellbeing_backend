from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    module: str
    entity_type: str | None
    entity_id: str | None
    description: str | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    user: AuditUserResponse | None = None


class AuditLogListData(BaseModel):
    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogListResponse(BaseModel):
    success: bool
    message: str
    data: AuditLogListData


class AuditLogDetailResponse(BaseModel):
    success: bool
    message: str
    data: AuditLogResponse