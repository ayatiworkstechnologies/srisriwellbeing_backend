from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.modules.rbac.model import (
    Permission,
    Role,
    RolePermission,
)
from seeds.permissions_seed import PATIENT_ROLE_PERMISSION_CODES


logger = logging.getLogger(__name__)


# When True, stale mappings for the default roles are removed and missing
# mappings from ROLE_PERMISSION_CODES are created.
#
# Custom roles are never changed.
SYNC_EXACT = True


COMMON_AUTH_PERMISSIONS = {
    "auth.login",
    "auth.logout",
    "auth.refresh_token",
    "auth.forgot_password",
    "auth.reset_password",
    "auth.change_password",
    "auth.view_current_user",
    "profile.view_own",
    "profile.update_own",
    "session.view_own",
    "session.revoke_own",
}


ADMIN_MANAGEMENT_PERMISSIONS = {
    "users.create",
    "users.view",
    "users.list",
    "users.update",
    "users.activate",
    "users.deactivate",
    "users.suspend",
    "users.unsuspend",
    "users.reset_password",
    "users.assign_role",
    "users.remove_role",
    "users.view_activity",
    "users.manage",

    "rbac.manage",

    "roles.create",
    "roles.view",
    "roles.list",
    "roles.update",
    "roles.delete",
    "roles.assign_permission",
    "roles.remove_permission",
    "roles.manage",

    "permissions.create",
    "permissions.view",
    "permissions.list",
    "permissions.update",
    "permissions.delete",
    "permissions.manage",

    "audit_logs.view",
    "audit_logs.list",
    "audit_logs.export",
    "user_activity.view",
}

ADMIN_PATIENT_PERMISSIONS = {
    "patient.view",
    "patient.list",
    "patient.search",
    "patient.activate",
    "patient.deactivate",
    "patient.archive",
    "patient.restore",
    "patient.view_sensitive_data",
    "patient.export",

    "patient_duplicate.view_matches",
    "patient_duplicate.override",
    "patient_duplicate.merge",
    "patient_duplicate.dismiss",

    "patient_address.view",
    "patient_identifier.view",

    "patient_document.view",
    "patient_document.download",
    "patient_document.verify",
}


ADMIN_WEEK_4_PERMISSIONS = {
    "medical_history.view",
    "medical_history.view_audit",

    "patient_condition.view",
    "patient_surgery.view",
    "existing_medicine.view",

    "allergy.view",
    "allergy.view_alert",

    "emergency_contact.view",

    "consent_template.create",
    "consent_template.view",
    "consent_template.list",
    "consent_template.update",
    "consent_template.activate",
    "consent_template.deactivate",
    "consent_template.delete",

    "patient_consent.view",
    "patient_consent.download",
    "patient_consent.verify",
}


# =========================================================
# WEEK 5 - APPOINTMENT MANAGEMENT
# =========================================================

ADMIN_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointments.create",
    "appointments.update",
    "appointments.confirm",
    "appointments.checkin",
    "appointments.consult",
    "appointments.complete",
    "appointments.reschedule",
    "appointments.no_show",
    "appointment_slots.view",
    "appointment_slots.manage",
    "doctor_availability.view",
    "doctor_availability.manage",
    "appointment_waiting_list.view",
    "appointment_waiting_list.manage",
}

RECEPTIONIST_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointments.create",
    "appointments.update",
    "appointments.confirm",
    "appointments.checkin",
    "appointments.reschedule",
    "appointments.no_show",
    "appointment_slots.view",
    "appointment_slots.manage",
    "doctor_availability.view",
    "appointment_waiting_list.view",
    "appointment_waiting_list.manage",
}

DUTY_DOCTOR_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointments.create",
    "appointments.consult",
    "appointments.complete",
    "appointments.reschedule",
    "appointment_slots.view",
    "doctor_availability.view",
    "doctor_availability.manage",
}

SPECIALIST_DOCTOR_WEEK_5_PERMISSIONS = {
    *DUTY_DOCTOR_WEEK_5_PERMISSIONS,
}

THERAPIST_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointment_slots.view",
    "doctor_availability.view",
}

PHARMACIST_WEEK_5_PERMISSIONS = {
    "appointments.view",
}


RECEPTIONIST_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    "patient.create",
    "patient.view",
    "patient.list",
    "patient.search",
    "patient.update",
    "patient.activate",
    "patient.deactivate",

    "patient_duplicate.check",
    "patient_duplicate.view_matches",
    "patient_duplicate.confirm_existing",
    "patient_duplicate.override",
    "patient_duplicate.dismiss",

    "patient_address.create",
    "patient_address.view",
    "patient_address.update",
    "patient_address.delete",

    "patient_identifier.create",
    "patient_identifier.view",
    "patient_identifier.update",
    "patient_identifier.deactivate",

    "patient_document.upload",
    "patient_document.view",
    "patient_document.download",
    "patient_document.update",

    "medical_history.view",
    "patient_condition.view",
    "patient_surgery.view",
    "existing_medicine.view",

    "allergy.view",
    "allergy.view_alert",

    "emergency_contact.create",
    "emergency_contact.view",
    "emergency_contact.update",
    "emergency_contact.delete",
    "emergency_contact.set_primary",
    "emergency_contact.verify",

    "consent_template.view",
    "consent_template.list",

    "patient_consent.create",
    "patient_consent.view",
    "patient_consent.capture",
    "patient_consent.upload",
    "patient_consent.download",
}


DUTY_DOCTOR_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    "patient.view",
    "patient.list",
    "patient.search",
    "patient.update",
    "patient.view_sensitive_data",

    "patient_duplicate.view_matches",

    "patient_address.view",
    "patient_identifier.view",

    "patient_document.upload",
    "patient_document.view",
    "patient_document.download",
    "patient_document.update",
    "patient_document.verify",

    "medical_history.create",
    "medical_history.view",
    "medical_history.update",
    "medical_history.view_audit",

    "patient_condition.create",
    "patient_condition.view",
    "patient_condition.update",
    "patient_condition.resolve",

    "patient_surgery.create",
    "patient_surgery.view",
    "patient_surgery.update",

    "existing_medicine.create",
    "existing_medicine.view",
    "existing_medicine.update",
    "existing_medicine.stop",

    "allergy.create",
    "allergy.view",
    "allergy.update",
    "allergy.deactivate",
    "allergy.view_alert",
    "allergy.acknowledge_alert",

    "emergency_contact.view",

    "consent_template.view",
    "consent_template.list",

    "patient_consent.view",
    "patient_consent.download",
    "patient_consent.verify",
}


SPECIALIST_DOCTOR_PERMISSIONS = {
    *DUTY_DOCTOR_PERMISSIONS,
}


THERAPIST_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    "patient.view",
    "patient.search",

    "patient_document.view",
    "patient_document.download",

    "medical_history.view",
    "patient_condition.view",
    "patient_surgery.view",
    "existing_medicine.view",

    "allergy.view",
    "allergy.view_alert",
    "allergy.acknowledge_alert",

    "emergency_contact.view",

    "consent_template.view",

    "patient_consent.view",
    "patient_consent.download",
}


PHARMACIST_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    "patient.view",
    "patient.search",

    "existing_medicine.view",

    "allergy.view",
    "allergy.view_alert",
    "allergy.acknowledge_alert",
}


ROLE_PERMISSION_CODES: dict[str, set[str]] = {
    "admin": {
        *COMMON_AUTH_PERMISSIONS,
        *ADMIN_MANAGEMENT_PERMISSIONS,
        *ADMIN_PATIENT_PERMISSIONS,
        *ADMIN_WEEK_4_PERMISSIONS,
        *ADMIN_WEEK_5_PERMISSIONS,
    },
    "receptionist": {
        *RECEPTIONIST_PERMISSIONS,
        *RECEPTIONIST_WEEK_5_PERMISSIONS,
    },
    "duty_doctor": {
        *DUTY_DOCTOR_PERMISSIONS,
        *DUTY_DOCTOR_WEEK_5_PERMISSIONS,
    },
    "specialist_doctor": {
        *SPECIALIST_DOCTOR_PERMISSIONS,
        *SPECIALIST_DOCTOR_WEEK_5_PERMISSIONS,
    },
    "therapist": {
        *THERAPIST_PERMISSIONS,
        *THERAPIST_WEEK_5_PERMISSIONS,
    },
    "pharmacist": {
        *PHARMACIST_PERMISSIONS,
        *PHARMACIST_WEEK_5_PERMISSIONS,
    },
    "patient": set(PATIENT_ROLE_PERMISSION_CODES),
}


ADMIN_FORBIDDEN_CLINICAL_PERMISSIONS = {
    "treatment_plan.create",
    "treatment_plan.update",
    "treatment_plan.prepare",
    "treatment_plan.review",
    "treatment_plan.recommend",
    "treatment_plan.approve",
    "treatment_plan.reject",
    "treatment_plan.finalize",
    "treatment_plan.revise",
    "treatment_plan.cancel",
}


def _columns(model: type[Any]) -> set[str]:
    return {
        column.key
        for column in model.__table__.columns
    }


def _permission_identifier_column() -> Any:
    """
    Prefer Permission.code.

    If the current Permission model stores permission codes in
    Permission.name, use that column instead.
    """
    columns = _columns(Permission)

    if "code" in columns:
        return Permission.code

    if "name" in columns:
        return Permission.name

    raise RuntimeError(
        "Permission model must contain either a 'code' "
        "or 'name' column."
    )


def _role_identifier_column() -> Any:
    """
    The current project schema uses Role.name for values such as:
    admin, receptionist and duty_doctor.

    Role.code is also supported if introduced later.
    """
    columns = _columns(Role)

    if "name" in columns:
        return Role.name

    if "code" in columns:
        return Role.code

    raise RuntimeError(
        "Role model must contain either a 'name' "
        "or 'code' column."
    )


def _mapping_values(
    *,
    role_id: Any,
    permission_id: Any,
) -> dict[str, Any]:
    values = {
        "role_id": role_id,
        "permission_id": permission_id,
        "is_active": True,
    }

    available = _columns(RolePermission)

    return {
        key: value
        for key, value in values.items()
        if key in available
    }


def validate_configuration() -> None:
    configured_roles = set(ROLE_PERMISSION_CODES)

    required_roles = {
        "admin",
        "receptionist",
        "duty_doctor",
        "specialist_doctor",
        "therapist",
        "pharmacist",
        "patient",
    }

    if configured_roles != required_roles:
        missing = required_roles - configured_roles
        unknown = configured_roles - required_roles

        raise ValueError(
            "Invalid role mapping configuration. "
            f"Missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )

    forbidden_admin_permissions = (
        ROLE_PERMISSION_CODES["admin"]
        & ADMIN_FORBIDDEN_CLINICAL_PERMISSIONS
    )

    if forbidden_admin_permissions:
        raise ValueError(
            "Admin cannot receive clinical treatment-plan "
            "permissions: "
            f"{sorted(forbidden_admin_permissions)}"
        )


async def load_roles(
    db: AsyncSession,
) -> dict[str, Role]:
    role_column = _role_identifier_column()
    role_names = set(ROLE_PERMISSION_CODES)

    result = await db.execute(
        select(Role).where(
            role_column.in_(role_names)
        )
    )

    role_rows = result.scalars().all()

    roles_by_name: dict[str, Role] = {}

    for role_row in role_rows:
        identifier = getattr(
            role_row,
            role_column.key,
        )
        roles_by_name[str(identifier)] = role_row

    missing_roles = role_names - set(roles_by_name)

    if missing_roles:
        raise RuntimeError(
            "The following roles do not exist. Run "
            "seeds/roles_seed.py first: "
            f"{sorted(missing_roles)}"
        )

    return roles_by_name


async def load_permissions(
    db: AsyncSession,
) -> dict[str, Permission]:
    permission_column = _permission_identifier_column()

    required_codes = {
        code
        for permission_codes in ROLE_PERMISSION_CODES.values()
        for code in permission_codes
    }

    result = await db.execute(
        select(Permission).where(
            permission_column.in_(required_codes)
        )
    )

    permission_rows = result.scalars().all()

    permissions_by_code: dict[str, Permission] = {}

    for permission_row in permission_rows:
        identifier = getattr(
            permission_row,
            permission_column.key,
        )
        permissions_by_code[str(identifier)] = (
            permission_row
        )

    missing_permissions = (
        required_codes
        - set(permissions_by_code)
    )

    if missing_permissions:
        preview = sorted(missing_permissions)

        raise RuntimeError(
            "Some permissions do not exist. Run the "
            "permission seed first. Missing permissions: "
            f"{preview}"
        )

    return permissions_by_code


async def synchronize_existing_default_role_mappings(
    db: AsyncSession,
    roles_by_name: dict[str, Role],
) -> tuple[int, set[tuple[Any, Any]]]:
    role_ids = [
        role.id
        for role in roles_by_name.values()
    ]

    desired_keys = {
        (
            roles_by_name[role_name].id,
            permission_code,
        )
        for role_name, permission_codes in ROLE_PERMISSION_CODES.items()
        for permission_code in permission_codes
    }

    result = await db.execute(
        select(
            RolePermission.id,
            RolePermission.role_id,
            Permission.code,
        )
        .join(
            Permission,
            Permission.id == RolePermission.permission_id,
        )
        .where(
            RolePermission.role_id.in_(role_ids)
        )
    )

    stale_ids: list[int] = []
    existing_keys: set[tuple[Any, Any]] = set()

    for mapping_id, role_id, permission_code in result.all():
        key = (role_id, permission_code)
        if key in desired_keys:
            existing_keys.add(key)
        else:
            stale_ids.append(mapping_id)

    if stale_ids:
        await db.execute(
            delete(RolePermission).where(
                RolePermission.id.in_(stale_ids)
            )
        )

    return len(stale_ids), existing_keys


async def existing_mapping_keys(
    db: AsyncSession,
    roles_by_name: dict[str, Role],
) -> set[tuple[Any, Any]]:
    role_ids = [
        role.id
        for role in roles_by_name.values()
    ]

    result = await db.execute(
        select(
            RolePermission.role_id,
            RolePermission.permission_id,
        ).where(
            RolePermission.role_id.in_(role_ids)
        )
    )

    return {
        (role_id, permission_id)
        for role_id, permission_id in result.all()
    }


async def seed_role_permissions(
    db: AsyncSession,
) -> dict[str, int]:
    """
    Synchronize Week 1-5 permissions for all default application roles.

    Execution order:
    1. Run Alembic migrations.
    2. Run roles_seed.py.
    3. Run permission_seed.py.
    4. Run this file.
    """
    validate_configuration()

    try:
        roles_by_name = await load_roles(db)
        permissions_by_code = await load_permissions(db)

        deleted = 0

        if SYNC_EXACT:
            deleted, existing_code_keys = (
                await synchronize_existing_default_role_mappings(
                    db=db,
                    roles_by_name=roles_by_name,
                )
            )
            existing_keys = {
                (
                    role_id,
                    permissions_by_code[permission_code].id,
                )
                for role_id, permission_code in existing_code_keys
            }
        else:
            existing_keys = await existing_mapping_keys(
                db,
                roles_by_name,
            )

        created = 0
        skipped = 0

        for role_name, permission_codes in (
            ROLE_PERMISSION_CODES.items()
        ):
            role_row = roles_by_name[role_name]

            for permission_code in sorted(
                permission_codes
            ):
                permission_row = permissions_by_code[
                    permission_code
                ]

                mapping_key = (
                    role_row.id,
                    permission_row.id,
                )

                if mapping_key in existing_keys:
                    skipped += 1
                    continue

                db.add(
                    RolePermission(
                        **_mapping_values(
                            role_id=role_row.id,
                            permission_id=permission_row.id,
                        )
                    )
                )

                existing_keys.add(mapping_key)
                created += 1

        await db.commit()

        return {
            "deleted": deleted,
            "created": created,
            "skipped": skipped,
            "roles": len(ROLE_PERMISSION_CODES),
        }

    except Exception:
        await db.rollback()
        raise


async def main() -> None:
    try:
        async with AsyncSessionLocal() as db:
            result = await seed_role_permissions(db)

        logger.info(
            "Role-permission seed completed: %s",
            result,
        )

        print(
            "Role-permission seed completed | "
            f"deleted={result['deleted']} | "
            f"created={result['created']} | "
            f"skipped={result['skipped']} | "
            f"roles={result['roles']}"
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )
    asyncio.run(main())