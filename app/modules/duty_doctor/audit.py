from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit_logs.service import AuditLogService


async def create_clinical_audit(
    db: AsyncSession,
    *,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    await AuditLogService.record(
        db=db,
        user_id=user_id,
        action=action,
        module="duty_doctor",
        entity_type=entity_type,
        entity_id=str(entity_id),
        description=description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
    )
