# flake8: noqa: E402
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.modules.rbac.model import Permission, Role
from app.modules.rbac.repository import RBACRepository
from seeds.permissions_seed import seed_permissions
from seeds.roles_seed import seed_roles

ROLE_PERMISSIONS = {
    "admin": {
        "users.manage",
        "users.view",
        "rbac.manage",
        "workflow.configure",
        "audit.view",
        "audit_logs.view",
        "patient.view",
        "reports.view",
    },
    "receptionist": {
        "patient.create",
        "patient.view",
        "patient.update",
        "appointment.create",
        "appointment.manage",
        "billing.collect",
        "consent.manage",
    },
    "duty_doctor": {
        "patient.view",
        "consultation.create",
        "medical_history.view",
        "medical_history.update",
        "allergy.manage",
        "treatment_plan.create",
        "treatment_plan.update",
        "treatment_plan.prepare",
        "treatment_plan.review",
        "treatment_plan.approve",
        "treatment_plan.finalize",
    },
    "specialist_doctor": {
        "patient.view",
        "consultation.create",
        "medical_history.view",
        "medical_history.update",
        "allergy.manage",
        "treatment_plan.create",
        "treatment_plan.update",
        "treatment_plan.prepare",
        "treatment_plan.review",
        "treatment_plan.approve",
        "treatment_plan.finalize",
    },
    "therapist": {
        "patient.view",
        "medical_history.view",
    },
    "pharmacist": {
        "patient.view",
        "medical_history.view",
        "pharmacy.dispense",
    },
}


async def main() -> None:
    try:
        async with AsyncSessionLocal() as db:
            await seed_roles(db)
            await seed_permissions(db)

            role_result = await db.execute(
                select(Role).where(Role.name.in_(ROLE_PERMISSIONS))
            )
            roles = {role.name: role for role in role_result.scalars()}

            required_codes = set().union(*ROLE_PERMISSIONS.values())
            permission_result = await db.execute(
                select(Permission).where(Permission.code.in_(required_codes))
            )
            permissions = {
                item.code: item for item in permission_result.scalars()
            }

            missing_codes = required_codes - permissions.keys()
            if missing_codes:
                raise RuntimeError(
                    f"Missing seeded permissions: {sorted(missing_codes)}"
                )

            for role_name, codes in ROLE_PERMISSIONS.items():
                await RBACRepository.replace_role_permissions(
                    db=db,
                    role_id=roles[role_name].id,
                    permission_ids=[permissions[code].id for code in codes],
                )
            await db.commit()
    finally:
        await engine.dispose()

    print("Roles, permissions and role mappings seeded successfully")


if __name__ == "__main__":
    asyncio.run(main())
