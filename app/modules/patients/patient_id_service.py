from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient


async def generate_patient_code(
    db: AsyncSession,
) -> str:
    current_year = datetime.utcnow().year

    prefix = f"SSW-{current_year}-"

    statement = select(
        func.count(Patient.id)
    ).where(
        Patient.patient_code.like(f"{prefix}%")
    )

    count = await db.scalar(statement)
    next_number = int(count or 0) + 1

    return f"{prefix}{next_number:06d}"