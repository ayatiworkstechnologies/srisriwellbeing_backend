import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.modules.rbac.model import Role


async def create_patient_role() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Role).where(Role.name == "patient"))

        existing_role = result.scalar_one_or_none()

        if existing_role:
            print(
                "Patient role already exists:",
                existing_role.id,
                existing_role.name,
            )
            return

        patient_role = Role(
            name="patient",
            display_name="Patient",
            description="Patient portal user",
            is_system=True,
            is_active=True,
        )

        db.add(patient_role)
        await db.commit()
        await db.refresh(patient_role)

        print(
            "Patient role created successfully:",
            patient_role.id,
        )


async def main() -> None:
    try:
        await create_patient_role()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
