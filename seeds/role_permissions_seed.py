from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


# =========================================================
# DIRECT SCRIPT EXECUTION SUPPORT
# =========================================================

# Supports:
#   python seeds/role_permissions_seed.py
#
# When executed directly, Python adds the "seeds" directory
# to sys.path. Add the repository root so "app" can be imported.
if __package__ in {None, ""}:
    sys.path.insert(
        0,
        str(Path(__file__).resolve().parents[1]),
    )


from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.modules.rbac.model import (  # noqa: E402
    Permission,
    Role,
    RolePermission,
)
from seeds.permissions_seed import (  # noqa: E402
    PATIENT_ROLE_PERMISSION_CODES,
)


logger = logging.getLogger(__name__)


# =========================================================
# SYNC MODE
# =========================================================
#
# SYNC_EXACT = True
# -----------------
# For the default application roles managed by this file:
# - remove their current role-permission mappings;
# - recreate exactly the mappings defined below.
#
# Custom roles are NOT changed.
#
# This is the safest option while the RBAC matrix is still
# being developed because stale permissions are removed.
# =========================================================

SYNC_EXACT = True


# =========================================================
# WEEK 1 - COMMON AUTH / PROFILE
# =========================================================

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


# =========================================================
# ADMIN - USER / RBAC / AUDIT
# =========================================================

ADMIN_MANAGEMENT_PERMISSIONS = {
    # Users
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

    # Application-level RBAC
    "rbac.manage",

    # Roles
    "roles.create",
    "roles.view",
    "roles.list",
    "roles.update",
    "roles.delete",
    "roles.assign_permission",
    "roles.remove_permission",
    "roles.manage",

    # Permissions
    "permissions.create",
    "permissions.view",
    "permissions.list",
    "permissions.update",
    "permissions.delete",
    "permissions.manage",

    # Audit
    "audit_logs.view",
    "audit_logs.list",
    "audit_logs.export",
    "user_activity.view",
}


# =========================================================
# ADMIN - PATIENT VISIBILITY
# =========================================================

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


# =========================================================
# ADMIN - WEEK 4
# =========================================================

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
# PATIENT BOOKING
# =========================================================

PATIENT_BOOKING_PERMISSIONS = {
    "patient_booking.create",
    "patient_booking.list",
    "patient_booking.view",
    "patient_booking.reschedule",
    "patient_booking.cancel",
}


# =========================================================
# WEEK 5 - APPOINTMENT MANAGEMENT
# =========================================================

# ---------------------------------------------------------
# ADMIN
# ---------------------------------------------------------
#
# Admin may supervise/configure appointment operations.
# Admin does NOT start or complete clinical consultations.
# ---------------------------------------------------------

ADMIN_WEEK_5_PERMISSIONS = {
    *PATIENT_BOOKING_PERMISSIONS,

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
    "doctor_availability.manage",

    "appointment_waiting_list.view",
    "appointment_waiting_list.manage",
}


# ---------------------------------------------------------
# RECEPTIONIST
# ---------------------------------------------------------
#
# Correct flow:
#
# Search/Register Patient
#       ↓
# Select Duty Doctor
#       ↓
# View Availability
#       ↓
# Select Slot
#       ↓
# Create Appointment
#       ↓
# Confirm
#       ↓
# Check-In
#       ↓
# CHECKED_IN
#       ↓
# Receptionist stops
#       ↓
# Duty Doctor takes over
#
# Receptionist does NOT:
# - start consultation
# - complete clinical consultation
# - enter vitals
# - enter clinical notes
# - enter diagnosis
# ---------------------------------------------------------

RECEPTIONIST_WEEK_5_PERMISSIONS = {
    *PATIENT_BOOKING_PERMISSIONS,

    "appointments.view",
    "appointments.create",
    "appointments.update",
    "appointments.confirm",
    "appointments.checkin",
    "appointments.reschedule",
    "appointments.no_show",

    # Receptionist only needs to select/view slots.
    "appointment_slots.view",

    # Receptionist views Duty Doctor schedule/availability.
    "doctor_availability.view",

    "appointment_waiting_list.view",
    "appointment_waiting_list.manage",
}


# ---------------------------------------------------------
# DUTY DOCTOR
# ---------------------------------------------------------
#
# Duty Doctor takes over after:
# appointment.status == CHECKED_IN
# ---------------------------------------------------------

DUTY_DOCTOR_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointments.consult",
    "appointments.complete",

    "appointment_slots.view",
    "doctor_availability.view",
}


# ---------------------------------------------------------
# SPECIALIST DOCTOR
# ---------------------------------------------------------

SPECIALIST_DOCTOR_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointment_slots.view",
    "doctor_availability.view",
}


# ---------------------------------------------------------
# THERAPIST
# ---------------------------------------------------------

THERAPIST_WEEK_5_PERMISSIONS = {
    "appointments.view",
    "appointment_slots.view",
    "doctor_availability.view",
}


# ---------------------------------------------------------
# PHARMACIST
# ---------------------------------------------------------

PHARMACIST_WEEK_5_PERMISSIONS = {
    "appointments.view",
}


# =========================================================
# WEEK 6 - DUTY DOCTOR CONSULTATION
# =========================================================

# ---------------------------------------------------------
# ADMIN
# ---------------------------------------------------------
#
# Admin receives view/audit access only.
# No Week 6 clinical-write permissions.
# ---------------------------------------------------------

ADMIN_WEEK_6_PERMISSIONS = {
    "consultations.view_all",
    "consultations.history",

    "patient_vitals.view",
    "clinical_notes.view",
    "diagnoses.view",
    "specialist_referrals.view",
    "case_shares.view",
}


# ---------------------------------------------------------
# DUTY DOCTOR
# ---------------------------------------------------------

DUTY_DOCTOR_WEEK_6_PERMISSIONS = {
    # Consultation
    "consultations.create",
    "consultations.view_own",
    "consultations.update",
    "consultations.status",
    "consultations.history",

    # Vitals
    "patient_vitals.view",
    "patient_vitals.manage",

    # Clinical notes
    "clinical_notes.view",
    "clinical_notes.manage",

    # Diagnosis
    "diagnoses.view",
    "diagnoses.manage",

    # Specialist referral
    "specialist_referrals.view",
    "specialist_referrals.manage",

    # Case sharing
    "case_shares.view",
    "case_shares.manage",
}


# ---------------------------------------------------------
# SPECIALIST DOCTOR
# ---------------------------------------------------------
#
# Week 6:
# Specialist gets read/review access to clinical information.
# Specialist-specific treatment-plan actions belong to Week 7.
# ---------------------------------------------------------

SPECIALIST_DOCTOR_WEEK_6_PERMISSIONS = {
    "consultations.history",

    "patient_vitals.view",
    "clinical_notes.view",
    "diagnoses.view",

    "specialist_referrals.view",
    "case_shares.view",
}


# ---------------------------------------------------------
# RECEPTIONIST / THERAPIST / PHARMACIST
# ---------------------------------------------------------

RECEPTIONIST_WEEK_6_PERMISSIONS: set[str] = set()

THERAPIST_WEEK_6_PERMISSIONS: set[str] = set()

PHARMACIST_WEEK_6_PERMISSIONS: set[str] = set()


# =========================================================
# RECEPTIONIST - WEEK 1 TO 4
# =========================================================

RECEPTIONIST_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    # Patient registration / lookup
    "patient.create",
    "patient.view",
    "patient.list",
    "patient.search",
    "patient.update",
    "patient.activate",
    "patient.deactivate",

    # Duplicate detection
    "patient_duplicate.check",
    "patient_duplicate.view_matches",
    "patient_duplicate.confirm_existing",
    "patient_duplicate.override",
    "patient_duplicate.dismiss",

    # Address
    "patient_address.create",
    "patient_address.view",
    "patient_address.update",
    "patient_address.delete",

    # Identifier
    "patient_identifier.create",
    "patient_identifier.view",
    "patient_identifier.update",
    "patient_identifier.deactivate",

    # Documents
    "patient_document.upload",
    "patient_document.view",
    "patient_document.download",
    "patient_document.update",

    # Read-only medical background
    "medical_history.view",
    "patient_condition.view",
    "patient_surgery.view",
    "existing_medicine.view",

    # Allergy visibility
    "allergy.view",
    "allergy.view_alert",

    # Emergency contacts
    "emergency_contact.create",
    "emergency_contact.view",
    "emergency_contact.update",
    "emergency_contact.delete",
    "emergency_contact.set_primary",
    "emergency_contact.verify",

    # Consent
    "consent_template.view",
    "consent_template.list",

    "patient_consent.create",
    "patient_consent.view",
    "patient_consent.capture",
    "patient_consent.upload",
    "patient_consent.download",
}


# =========================================================
# DUTY DOCTOR - WEEK 1 TO 4
# =========================================================

DUTY_DOCTOR_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    # Patient
    "patient.view",
    "patient.list",
    "patient.search",
    "patient.update",
    "patient.view_sensitive_data",

    "patient_duplicate.view_matches",

    # Address / identifiers
    "patient_address.view",
    "patient_identifier.view",

    # Documents
    "patient_document.upload",
    "patient_document.view",
    "patient_document.download",
    "patient_document.update",
    "patient_document.verify",

    # Medical history
    "medical_history.create",
    "medical_history.view",
    "medical_history.update",
    "medical_history.view_audit",

    # Conditions
    "patient_condition.create",
    "patient_condition.view",
    "patient_condition.update",
    "patient_condition.resolve",

    # Surgeries
    "patient_surgery.create",
    "patient_surgery.view",
    "patient_surgery.update",

    # Existing medicines
    "existing_medicine.create",
    "existing_medicine.view",
    "existing_medicine.update",
    "existing_medicine.stop",

    # Allergies
    "allergy.create",
    "allergy.view",
    "allergy.update",
    "allergy.deactivate",
    "allergy.view_alert",
    "allergy.acknowledge_alert",

    # Emergency contact
    "emergency_contact.view",

    # Consent
    "consent_template.view",
    "consent_template.list",

    "patient_consent.view",
    "patient_consent.download",
    "patient_consent.verify",
}


# =========================================================
# SPECIALIST DOCTOR - BASE
# =========================================================

SPECIALIST_DOCTOR_PERMISSIONS = {
    *DUTY_DOCTOR_PERMISSIONS,
}


# =========================================================
# THERAPIST - BASE
# =========================================================

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


# =========================================================
# PHARMACIST - BASE
# =========================================================

PHARMACIST_PERMISSIONS = {
    *COMMON_AUTH_PERMISSIONS,

    "patient.view",
    "patient.search",

    "existing_medicine.view",

    "allergy.view",
    "allergy.view_alert",
    "allergy.acknowledge_alert",
}


# =========================================================
# FINAL ROLE -> PERMISSION MAP
# =========================================================

ROLE_PERMISSION_CODES: dict[str, set[str]] = {
    "admin": {
        *COMMON_AUTH_PERMISSIONS,
        *ADMIN_MANAGEMENT_PERMISSIONS,
        *ADMIN_PATIENT_PERMISSIONS,
        *ADMIN_WEEK_4_PERMISSIONS,
        *ADMIN_WEEK_5_PERMISSIONS,
        *ADMIN_WEEK_6_PERMISSIONS,
    },

    "receptionist": {
        *RECEPTIONIST_PERMISSIONS,
        *RECEPTIONIST_WEEK_5_PERMISSIONS,
        *RECEPTIONIST_WEEK_6_PERMISSIONS,
    },

    "duty_doctor": {
        *DUTY_DOCTOR_PERMISSIONS,
        *DUTY_DOCTOR_WEEK_5_PERMISSIONS,
        *DUTY_DOCTOR_WEEK_6_PERMISSIONS,
    },

    "specialist_doctor": {
        *SPECIALIST_DOCTOR_PERMISSIONS,
        *SPECIALIST_DOCTOR_WEEK_5_PERMISSIONS,
        *SPECIALIST_DOCTOR_WEEK_6_PERMISSIONS,
    },

    "therapist": {
        *THERAPIST_PERMISSIONS,
        *THERAPIST_WEEK_5_PERMISSIONS,
        *THERAPIST_WEEK_6_PERMISSIONS,
    },

    "pharmacist": {
        *PHARMACIST_PERMISSIONS,
        *PHARMACIST_WEEK_5_PERMISSIONS,
        *PHARMACIST_WEEK_6_PERMISSIONS,
    },

    "patient": set(
        PATIENT_ROLE_PERMISSION_CODES
    ),
}


# =========================================================
# CLINICAL SAFETY RULES
# =========================================================

# Admin may supervise clinical records but does not perform
# clinical actions.
ADMIN_FORBIDDEN_CLINICAL_PERMISSIONS = {
    # Appointment clinical handoff
    "appointments.consult",
    "appointments.complete",

    # Week 6 writes
    "consultations.create",
    "consultations.update",
    "consultations.status",

    "patient_vitals.manage",
    "clinical_notes.manage",
    "diagnoses.manage",
    "specialist_referrals.manage",
    "case_shares.manage",

    # Treatment-plan writes/approval
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


# Receptionist must stop at CHECKED_IN.
RECEPTIONIST_FORBIDDEN_CLINICAL_PERMISSIONS = {
    "appointments.consult",
    "appointments.complete",

    "consultations.create",
    "consultations.update",
    "consultations.status",

    "patient_vitals.manage",
    "clinical_notes.manage",
    "diagnoses.manage",
    "specialist_referrals.manage",
    "case_shares.manage",
}


# =========================================================
# SQLALCHEMY MODEL HELPERS
# =========================================================

def _columns(
    model: type[Any],
) -> set[str]:
    return {
        column.key
        for column
        in model.__table__.columns
    }


def _permission_identifier_column() -> Any:
    """
    Prefer Permission.code.

    Your permissions seed uses codes such as:
      appointments.view
      appointments.checkin
      consultations.create
    """

    columns = _columns(
        Permission
    )

    if "code" in columns:
        return Permission.code

    # Backward compatibility only.
    if "name" in columns:
        return Permission.name

    raise RuntimeError(
        "Permission model must contain "
        "either 'code' or 'name'."
    )


def _role_identifier_column() -> Any:
    """
    Prefer Role.code.

    roles_seed.py creates rows such as:

      code = "admin"
      name = "Admin"

      code = "receptionist"
      name = "Receptionist"

      code = "duty_doctor"
      name = "Duty Doctor"

    ROLE_PERMISSION_CODES uses the machine codes,
    therefore Role.code is the correct identifier.
    """

    columns = _columns(
        Role
    )

    if "code" in columns:
        return Role.code

    # Backward compatibility only.
    if "name" in columns:
        return Role.name

    raise RuntimeError(
        "Role model must contain "
        "either 'code' or 'name'."
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

    available_columns = _columns(
        RolePermission
    )

    return {
        key: value
        for key, value
        in values.items()
        if key in available_columns
    }


# =========================================================
# CONFIGURATION VALIDATION
# =========================================================

def validate_configuration() -> None:

    required_roles = {
        "admin",
        "receptionist",
        "duty_doctor",
        "specialist_doctor",
        "therapist",
        "pharmacist",
        "patient",
    }

    configured_roles = set(
        ROLE_PERMISSION_CODES
    )

    if configured_roles != required_roles:

        missing = (
            required_roles
            - configured_roles
        )

        unknown = (
            configured_roles
            - required_roles
        )

        raise ValueError(
            "Invalid role mapping configuration. "
            f"Missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )

    # -----------------------------------------------------
    # ADMIN SAFETY
    # -----------------------------------------------------

    admin_forbidden = (
        ROLE_PERMISSION_CODES[
            "admin"
        ]
        & ADMIN_FORBIDDEN_CLINICAL_PERMISSIONS
    )

    if admin_forbidden:
        raise ValueError(
            "Admin cannot receive forbidden "
            "clinical permissions: "
            f"{sorted(admin_forbidden)}"
        )

    # -----------------------------------------------------
    # RECEPTIONIST SAFETY
    # -----------------------------------------------------

    receptionist_forbidden = (
        ROLE_PERMISSION_CODES[
            "receptionist"
        ]
        & RECEPTIONIST_FORBIDDEN_CLINICAL_PERMISSIONS
    )

    if receptionist_forbidden:
        raise ValueError(
            "Receptionist cannot receive "
            "clinical consultation permissions: "
            f"{sorted(receptionist_forbidden)}"
        )

    # -----------------------------------------------------
    # DUTY DOCTOR HANDOFF REQUIREMENTS
    # -----------------------------------------------------

    required_duty_doctor_permissions = {
        "appointments.view",
        "appointments.consult",
        "appointments.complete",
        "consultations.create",
        "consultations.view_own",
    }

    missing_duty_doctor_permissions = (
        required_duty_doctor_permissions
        - ROLE_PERMISSION_CODES[
            "duty_doctor"
        ]
    )

    if missing_duty_doctor_permissions:
        raise ValueError(
            "Duty Doctor is missing required "
            "appointment/consultation permissions: "
            f"{sorted(missing_duty_doctor_permissions)}"
        )

    # -----------------------------------------------------
    # RECEPTIONIST HANDOFF REQUIREMENTS
    # -----------------------------------------------------

    required_receptionist_permissions = {
        "patient.search",
        "appointments.view",
        "appointments.create",
        "appointments.confirm",
        "appointments.checkin",
        "appointment_slots.view",
        "doctor_availability.view",
    }

    missing_receptionist_permissions = (
        required_receptionist_permissions
        - ROLE_PERMISSION_CODES[
            "receptionist"
        ]
    )

    if missing_receptionist_permissions:
        raise ValueError(
            "Receptionist is missing required "
            "appointment handoff permissions: "
            f"{sorted(missing_receptionist_permissions)}"
        )


# =========================================================
# LOAD DEFAULT ROLES
# =========================================================

async def load_roles(
    db: AsyncSession,
) -> dict[str, Role]:

    role_column = (
        _role_identifier_column()
    )

    role_codes = set(
        ROLE_PERMISSION_CODES
    )

    result = await db.execute(
        select(
            Role
        ).where(
            role_column.in_(
                role_codes
            )
        )
    )

    role_rows = (
        result
        .scalars()
        .all()
    )

    roles_by_code: dict[
        str,
        Role,
    ] = {}

    for role_row in role_rows:

        identifier = getattr(
            role_row,
            role_column.key,
        )

        roles_by_code[
            str(identifier)
        ] = role_row

    missing_roles = (
        role_codes
        - set(
            roles_by_code
        )
    )

    if missing_roles:
        raise RuntimeError(
            "The following roles do not exist. "
            "Run seeds/roles_seed.py first. "
            f"Missing roles: {sorted(missing_roles)}"
        )

    return roles_by_code


# =========================================================
# LOAD PERMISSIONS
# =========================================================

async def load_permissions(
    db: AsyncSession,
) -> dict[str, Permission]:

    permission_column = (
        _permission_identifier_column()
    )

    required_codes = {
        permission_code

        for permission_codes
        in ROLE_PERMISSION_CODES.values()

        for permission_code
        in permission_codes
    }

    result = await db.execute(
        select(
            Permission
        ).where(
            permission_column.in_(
                required_codes
            )
        )
    )

    permission_rows = (
        result
        .scalars()
        .all()
    )

    permissions_by_code: dict[
        str,
        Permission,
    ] = {}

    for permission_row in permission_rows:

        identifier = getattr(
            permission_row,
            permission_column.key,
        )

        permissions_by_code[
            str(identifier)
        ] = permission_row

    missing_permissions = (
        required_codes
        - set(
            permissions_by_code
        )
    )

    if missing_permissions:
        raise RuntimeError(
            "Some required permissions do not exist. "
            "Run seeds/permissions_seed.py first. "
            "Missing permissions: "
            f"{sorted(missing_permissions)}"
        )

    return permissions_by_code


# =========================================================
# EXISTING MAPPING HELPERS
# =========================================================

async def existing_mapping_keys(
    db: AsyncSession,
    roles_by_code: dict[str, Role],
) -> set[tuple[Any, Any]]:

    role_ids = [
        role.id
        for role
        in roles_by_code.values()
    ]

    result = await db.execute(
        select(
            RolePermission.role_id,
            RolePermission.permission_id,
        ).where(
            RolePermission.role_id.in_(
                role_ids
            )
        )
    )

    return {
        (
            role_id,
            permission_id,
        )

        for (
            role_id,
            permission_id,
        )
        in result.all()
    }


async def remove_existing_default_role_mappings(
    db: AsyncSession,
    roles_by_code: dict[str, Role],
) -> int:
    """
    Remove mappings ONLY for roles configured in this seed.

    Custom roles and their mappings are not touched.
    """

    role_ids = [
        role.id
        for role
        in roles_by_code.values()
    ]

    result = await db.execute(
        delete(
            RolePermission
        ).where(
            RolePermission.role_id.in_(
                role_ids
            )
        )
    )

    return int(
        result.rowcount
        or 0
    )


# =========================================================
# SEED ROLE PERMISSIONS
# =========================================================

async def seed_role_permissions(
    db: AsyncSession,
) -> dict[str, int]:
    """
    Synchronize Week 1-6 permissions for all default roles.

    Correct execution order:

    1.
    python seeds/roles_seed.py

    2.
    python seeds/permissions_seed.py

    3.
    python seeds/role_permissions_seed.py
    """

    validate_configuration()

    try:

        roles_by_code = (
            await load_roles(
                db
            )
        )

        permissions_by_code = (
            await load_permissions(
                db
            )
        )

        deleted = 0

        if SYNC_EXACT:

            deleted = (
                await remove_existing_default_role_mappings(
                    db=db,
                    roles_by_code=roles_by_code,
                )
            )

            existing_keys: set[
                tuple[Any, Any]
            ] = set()

        else:

            existing_keys = (
                await existing_mapping_keys(
                    db=db,
                    roles_by_code=roles_by_code,
                )
            )

        created = 0
        skipped = 0

        for (
            role_code,
            permission_codes,
        ) in ROLE_PERMISSION_CODES.items():

            role_row = (
                roles_by_code[
                    role_code
                ]
            )

            for permission_code in sorted(
                permission_codes
            ):

                permission_row = (
                    permissions_by_code[
                        permission_code
                    ]
                )

                mapping_key = (
                    role_row.id,
                    permission_row.id,
                )

                if (
                    mapping_key
                    in existing_keys
                ):
                    skipped += 1
                    continue

                db.add(
                    RolePermission(
                        **_mapping_values(
                            role_id=(
                                role_row.id
                            ),
                            permission_id=(
                                permission_row.id
                            ),
                        )
                    )
                )

                existing_keys.add(
                    mapping_key
                )

                created += 1

        await db.commit()

        return {
            "deleted": deleted,
            "created": created,
            "skipped": skipped,
            "roles": len(
                ROLE_PERMISSION_CODES
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

            result = (
                await seed_role_permissions(
                    db
                )
            )

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
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    asyncio.run(
        main()
    )