from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Support direct execution with ``python seeds/roles_seed.py``. In that mode,
# Python adds ``seeds`` (not the repository root) to the import search path.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.modules.rbac.model import Role  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RoleSeed:
    code: str
    name: str
    description: str


DEFAULT_ROLES: tuple[RoleSeed, ...] = (
    RoleSeed(
        code="admin",
        name="Admin",
        description=(
            "Manages users, roles, permissions, workflows, "
            "configuration and audit access. Admin must not "
            "create, approve or modify clinical treatment plans."
        ),
    ),
    RoleSeed(
        code="receptionist",
        name="Receptionist",
        description=(
            "Registers patients, manages demographic details, "
            "appointments, documents, consent and front-desk workflows."
        ),
    ),
    RoleSeed(
        code="duty_doctor",
        name="Duty Doctor",
        description=(
            "Performs patient assessment, diagnosis, clinical "
            "documentation and treatment-plan preparation."
        ),
    ),
    RoleSeed(
        code="specialist_doctor",
        name="Specialist Doctor",
        description=(
            "Reviews complex cases, provides specialist recommendations "
            "and approves authorized clinical treatment plans."
        ),
    ),
    RoleSeed(
        code="therapist",
        name="Therapist",
        description=(
            "Views assigned patient records and performs therapy sessions "
            "according to approved treatment plans."
        ),
    ),
    RoleSeed(
        code="pharmacist",
        name="Pharmacist",
        description=(
            "Manages medicines, inventory, prescription verification "
            "and medicine dispensing."
        ),
    ),
    RoleSeed(
        code="patient",
        name="Patient",
        description=(
            "Uses the patient portal to manage their own profile, "
            "documents, clinical records and consents."
        ),
    ),
)


def _role_values(seed: RoleSeed) -> dict:
    """
    Return only fields that exist in the Role SQLAlchemy model.

    Required field:
    - code

    Supported optional fields:
    - name
    - description
    - is_active
    - is_system
    - is_system_role
    """
    available_columns = {column.key for column in Role.__table__.columns}

    values = {
        "name": seed.code,
        "display_name": seed.name,
        "description": seed.description,
        "is_active": True,
        "is_system": True,
        "is_system_role": True,
    }

    return {
        key: value for key, value in values.items() if key in available_columns
    }


def _update_role(
    role: Role,
    seed: RoleSeed,
) -> None:
    available_columns = {column.key for column in Role.__table__.columns}

    values = {
        "name": seed.code,
        "display_name": seed.name,
        "description": seed.description,
        "is_active": True,
        "is_system": True,
        "is_system_role": True,
    }

    for key, value in values.items():
        if key in available_columns:
            setattr(role, key, value)


async def seed_roles(
    db: AsyncSession,
) -> dict[str, int]:
    """
    Create or update all default application roles.

    This function is idempotent:
    - existing roles are found using Role.name;
    - existing rows are updated;
    - duplicate roles are not created.
    """
    created = 0
    updated = 0

    try:
        for seed in DEFAULT_ROLES:
            result = await db.execute(
                select(Role).where(Role.name == seed.code)
            )
            existing_role = result.scalar_one_or_none()

            if existing_role is None:
                db.add(Role(**_role_values(seed)))
                created += 1
            else:
                _update_role(
                    existing_role,
                    seed,
                )
                updated += 1

        await db.commit()

        return {
            "created": created,
            "updated": updated,
            "total": len(DEFAULT_ROLES),
        }

    except Exception:
        await db.rollback()
        raise


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await seed_roles(db)
    await engine.dispose()

    logger.info(
        "Role seed completed: %s",
        result,
    )
    print(
        "Role seed completed | "
        f"created={result['created']} | "
        f"updated={result['updated']} | "
        f"total={result['total']}"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | " "%(name)s | %(message)s"),
    )
    asyncio.run(main())
