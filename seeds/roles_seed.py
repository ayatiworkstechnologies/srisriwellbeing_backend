from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


# =========================================================
# DIRECT SCRIPT EXECUTION SUPPORT
# =========================================================
#
# Supports:
#   python seeds/roles_seed.py
#
# When executed directly, Python adds "seeds" instead of the
# repository root to sys.path. Add the repository root so
# imports from app.* work correctly.
# =========================================================

if __package__ in {None, ""}:
    sys.path.insert(
        0,
        str(Path(__file__).resolve().parents[1]),
    )


from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.modules.rbac.model import Role  # noqa: E402


logger = logging.getLogger(__name__)


# =========================================================
# ROLE SEED DEFINITION
# =========================================================


@dataclass(frozen=True, slots=True)
class RoleSeed:
    code: str
    display_name: str
    description: str


# =========================================================
# DEFAULT SYSTEM ROLES
# =========================================================
#
# IMPORTANT:
#
# Machine value:
#   admin
#   receptionist
#   duty_doctor
#   specialist_doctor
#   therapist
#   pharmacist
#   patient
#
# Display value:
#   Admin
#   Receptionist
#   Duty Doctor
#   Specialist Doctor
#   Therapist
#   Pharmacist
#   Patient
#
# For compatibility with the current RBAC service:
#
#   Role.code         = machine value, when column exists
#   Role.name         = machine value
#   Role.display_name = human-readable label
#
# Example:
#
#   code         = "duty_doctor"
#   name         = "duty_doctor"
#   display_name = "Duty Doctor"
# =========================================================


DEFAULT_ROLES: tuple[RoleSeed, ...] = (
    RoleSeed(
        code="admin",
        display_name="Admin",
        description=(
            "Manages users, roles, permissions, workflows, "
            "configuration and audit access. Admin must not "
            "create, approve or modify clinical treatment plans."
        ),
    ),
    RoleSeed(
        code="receptionist",
        display_name="Receptionist",
        description=(
            "Registers and searches patients, manages front-desk "
            "patient information, creates appointments, checks "
            "Duty Doctor availability, selects appointment slots, "
            "confirms appointments, manages waiting-list operations "
            "and checks patients in before the clinical handoff."
        ),
    ),
    RoleSeed(
        code="duty_doctor",
        display_name="Duty Doctor",
        description=(
            "Receives checked-in patients from Reception, performs "
            "initial consultation, records vital signs, clinical "
            "notes, medical assessment, observations and diagnosis, "
            "and creates specialist referrals or case shares when "
            "required."
        ),
    ),
    RoleSeed(
        code="specialist_doctor",
        display_name="Specialist Doctor",
        description=(
            "Reviews referred or shared clinical cases, provides "
            "specialist recommendations and performs authorized "
            "specialist clinical workflows."
        ),
    ),
    RoleSeed(
        code="therapist",
        display_name="Therapist",
        description=(
            "Views assigned patient records and performs therapy "
            "sessions according to authorized treatment plans."
        ),
    ),
    RoleSeed(
        code="pharmacist",
        display_name="Pharmacist",
        description=(
            "Manages medicines, inventory, prescription verification "
            "and authorized medicine dispensing."
        ),
    ),
    RoleSeed(
        code="patient",
        display_name="Patient",
        description=(
            "Uses the patient portal to access and manage authorized "
            "parts of their own profile, documents, appointments, "
            "clinical records and consents."
        ),
    ),
)


# =========================================================
# MODEL HELPERS
# =========================================================


def _columns(
    model: type[Any],
) -> set[str]:
    return {
        column.key
        for column in model.__table__.columns
    }


def _role_values(
    seed: RoleSeed,
) -> dict[str, Any]:
    """
    Return only fields supported by the current Role model.

    Current project convention:

        code         = machine identifier
        name         = machine identifier
        display_name = UI label

    Example:

        code         = duty_doctor
        name         = duty_doctor
        display_name = Duty Doctor
    """

    available_columns = _columns(Role)

    values: dict[str, Any] = {
        "code": seed.code,
        "name": seed.code,
        "display_name": seed.display_name,
        "description": seed.description,
        "is_active": True,
        "is_system": True,
        "is_system_role": True,
    }

    return {
        key: value
        for key, value in values.items()
        if key in available_columns
    }


def _update_role(
    role: Role,
    seed: RoleSeed,
) -> None:
    """
    Normalize an existing default role.

    This also repairs older rows where:
    - code is NULL/missing but name contains the machine role; or
    - display_name is missing/outdated.
    """

    values = _role_values(seed)

    for key, value in values.items():
        setattr(
            role,
            key,
            value,
        )


# =========================================================
# FIND EXISTING ROLE
# =========================================================


async def _find_existing_role(
    db: AsyncSession,
    seed: RoleSeed,
) -> Role | None:
    """
    Find an existing role safely.

    Preferred lookup:
        Role.code == seed.code

    Compatibility lookup:
        Role.name == seed.code

    Using both prevents duplicate role creation while migrating
    older data that stored only the machine identifier in name.
    """

    columns = _columns(Role)

    filters = []

    if "code" in columns:
        filters.append(
            Role.code == seed.code
        )

    if "name" in columns:
        filters.append(
            Role.name == seed.code
        )

    if not filters:
        raise RuntimeError(
            "Role model must contain at least "
            "a 'code' or 'name' column."
        )

    if len(filters) == 1:
        condition = filters[0]
    else:
        condition = or_(
            *filters
        )

    result = await db.execute(
        select(Role)
        .where(condition)
        .order_by(Role.id.asc())
        .limit(1)
    )

    return result.scalar_one_or_none()


# =========================================================
# VALIDATE DEFAULT ROLE CONFIGURATION
# =========================================================


def validate_default_roles() -> None:
    codes = [
        role.code
        for role in DEFAULT_ROLES
    ]

    duplicate_codes = {
        code
        for code in codes
        if codes.count(code) > 1
    }

    if duplicate_codes:
        raise ValueError(
            "Duplicate default role codes found: "
            f"{sorted(duplicate_codes)}"
        )

    required_codes = {
        "admin",
        "receptionist",
        "duty_doctor",
        "specialist_doctor",
        "therapist",
        "pharmacist",
        "patient",
    }

    configured_codes = set(
        codes
    )

    if configured_codes != required_codes:
        missing = (
            required_codes
            - configured_codes
        )

        unknown = (
            configured_codes
            - required_codes
        )

        raise ValueError(
            "Invalid default role configuration. "
            f"Missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )


# =========================================================
# SEED ROLES
# =========================================================


async def seed_roles(
    db: AsyncSession,
) -> dict[str, int]:
    """
    Create or normalize all seven default application roles.

    Idempotent behavior:
    - existing rows are found by Role.code OR Role.name;
    - existing rows are normalized;
    - missing rows are created;
    - duplicate rows are not intentionally created.

    Run this before:
        python seeds/permissions_seed.py
        python seeds/role_permissions_seed.py
    """

    validate_default_roles()

    created = 0
    updated = 0

    try:
        for seed in DEFAULT_ROLES:

            existing_role = (
                await _find_existing_role(
                    db=db,
                    seed=seed,
                )
            )

            if existing_role is None:

                role_values = (
                    _role_values(
                        seed
                    )
                )

                if not role_values:
                    raise RuntimeError(
                        "No supported Role fields "
                        "were found for seeding."
                    )

                db.add(
                    Role(
                        **role_values
                    )
                )

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
            "total": len(
                DEFAULT_ROLES
            ),
        }

    except Exception:
        await db.rollback()
        raise


# =========================================================
# MAIN
# =========================================================


async def main() -> None:

    try:
        async with AsyncSessionLocal() as db:

            result = await seed_roles(
                db
            )

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

    finally:
        await engine.dispose()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    asyncio.run(
        main()
    )