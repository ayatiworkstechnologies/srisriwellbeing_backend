from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit_logs.model import AuditLog


class AuditLogRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        user_id: int | None,
        action: str,
        module: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        description: str | None = None,
        old_values: dict | list | None = None,
        new_values: dict | list | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        safe_old_values: Any = (
            jsonable_encoder(old_values)
            if old_values is not None
            else None
        )

        safe_new_values: Any = (
            jsonable_encoder(new_values)
            if new_values is not None
            else None
        )

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=safe_old_values,
            new_values=safe_new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit_log)

        await db.flush()
        await db.refresh(audit_log)

        return audit_log

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        audit_log_id: int,
    ) -> AuditLog | None:
        result = await db.execute(
            select(AuditLog)
            .options(
                selectinload(AuditLog.user),
            )
            .where(
                AuditLog.id == audit_log_id
            )
        )

        return result.scalar_one_or_none()

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
    ) -> tuple[list[AuditLog], int]:
        filters = []

        if user_id is not None:
            filters.append(
                AuditLog.user_id == user_id
            )

        if action:
            filters.append(
                AuditLog.action == action
            )

        if module:
            filters.append(
                AuditLog.module == module
            )

        if entity_type:
            filters.append(
                AuditLog.entity_type == entity_type
            )

        if entity_id:
            filters.append(
                AuditLog.entity_id == entity_id
            )

        if date_from:
            filters.append(
                AuditLog.created_at >= date_from
            )

        if date_to:
            filters.append(
                AuditLog.created_at <= date_to
            )

        count_result = await db.execute(
            select(
                func.count(AuditLog.id)
            ).where(
                *filters
            )
        )

        total = count_result.scalar_one()

        result = await db.execute(
            select(AuditLog)
            .options(
                selectinload(AuditLog.user),
            )
            .where(
                *filters
            )
            .order_by(
                AuditLog.id.desc()
            )
            .offset(skip)
            .limit(limit)
        )

        logs = list(
            result.scalars().all()
        )

        return logs, total
