from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.modules.audit_logs.schema import (
    AuditLogDetailResponse,
    AuditLogListData,
    AuditLogListResponse,
    AuditLogResponse,
)
from app.modules.audit_logs.service import AuditLogService
from app.modules.users.model import User




router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=AuditLogListResponse,
)
async def list_audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int | None = None,
    action: str | None = None,
    module: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("audit_logs.view")
    ),
):
    items, total = await AuditLogService.list_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        module=module,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
    )

    return AuditLogListResponse(
        success=True,
        message="Audit logs fetched successfully",
        data=AuditLogListData(
            items=[
                AuditLogResponse.model_validate(item)
                for item in items
            ],
            total=total,
            skip=skip,
            limit=limit,
        ),
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogDetailResponse,
)
async def get_audit_log(
    audit_log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("audit_logs.view")
    ),
):
    audit_log = await AuditLogService.get_by_id(
        db,
        audit_log_id,
    )

    return AuditLogDetailResponse(
        success=True,
        message="Audit log fetched successfully",
        data=AuditLogResponse.model_validate(
            audit_log
        ),
    )