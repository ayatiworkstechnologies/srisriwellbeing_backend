from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit_logs.repository import (
    AuditLogRepository,
)


class AuditLogService:
    @staticmethod
    async def record(
        db: AsyncSession,
        *,
        user_id: int | None,
        action: str,
        module: str,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        description: str | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        return await AuditLogRepository.create(
            db=db,
            user_id=user_id,
            action=action,
            module=module,
            entity_type=entity_type,
            entity_id=(str(entity_id) if entity_id is not None else None),
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        audit_log_id: int,
    ):
        audit_log = await AuditLogRepository.get_by_id(
            db,
            audit_log_id,
        )

        if audit_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found",
            )

        return audit_log

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        *,
        skip: int,
        limit: int,
        user_id: int | None = None,
        action: str | None = None,
        module: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        return await AuditLogRepository.list_logs(
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
