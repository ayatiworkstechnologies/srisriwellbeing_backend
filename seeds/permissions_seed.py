from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Support direct execution with ``python seeds/permissions_seed.py``. In that
# mode, Python adds ``seeds`` rather than the repository root to ``sys.path``.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.modules.rbac.model import Permission  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PermissionSeed:
    code: str
    name: str
    module: str
    description: str


def permission(
    code: str,
    name: str,
    module: str,
    description: str,
) -> PermissionSeed:
    return PermissionSeed(
        code=code,
        name=name,
        module=module,
        description=description,
    )


WEEK_1_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "auth.login",
        "Login",
        "auth",
        "Authenticate using email and password.",
    ),
    permission(
        "auth.logout",
        "Logout",
        "auth",
        "End the current authenticated session.",
    ),
    permission(
        "auth.refresh_token",
        "Refresh Access Token",
        "auth",
        "Create a new access token using a valid refresh token.",
    ),
    permission(
        "auth.forgot_password",
        "Forgot Password",
        "auth",
        "Request a password-reset workflow.",
    ),
    permission(
        "auth.reset_password",
        "Reset Password",
        "auth",
        "Reset a password using a valid reset token.",
    ),
    permission(
        "auth.change_password",
        "Change Own Password",
        "auth",
        "Change the authenticated user's password.",
    ),
    permission(
        "auth.view_current_user",
        "View Current User",
        "auth",
        "View the authenticated user's identity, roles and permissions.",
    ),
    permission(
        "profile.view_own",
        "View Own Profile",
        "profile",
        "View the authenticated user's profile.",
    ),
    permission(
        "profile.update_own",
        "Update Own Profile",
        "profile",
        "Update the authenticated user's profile.",
    ),
    permission(
        "session.view_own",
        "View Own Sessions",
        "session",
        "View the authenticated user's active sessions.",
    ),
    permission(
        "session.revoke_own",
        "Revoke Own Sessions",
        "session",
        "Revoke one or more sessions owned by the authenticated user.",
    ),
)


WEEK_2_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "users.create",
        "Create User",
        "users",
        "Create an application user.",
    ),
    permission(
        "users.view",
        "View User",
        "users",
        "View a user account.",
    ),
    permission(
        "users.list",
        "List Users",
        "users",
        "List and search user accounts.",
    ),
    permission(
        "users.update",
        "Update User",
        "users",
        "Update a user account.",
    ),
    permission(
        "users.activate",
        "Activate User",
        "users",
        "Activate a user account.",
    ),
    permission(
        "users.deactivate",
        "Deactivate User",
        "users",
        "Deactivate a user account.",
    ),
    permission(
        "users.suspend",
        "Suspend User",
        "users",
        "Suspend a user account.",
    ),
    permission(
        "users.unsuspend",
        "Unsuspend User",
        "users",
        "Remove a user suspension.",
    ),
    permission(
        "users.reset_password",
        "Reset User Password",
        "users",
        "Administratively initiate a user password reset.",
    ),
    permission(
        "users.assign_role",
        "Assign User Role",
        "users",
        "Assign a role to a user.",
    ),
    permission(
        "users.remove_role",
        "Remove User Role",
        "users",
        "Remove a role from a user.",
    ),
    permission(
        "users.view_activity",
        "View User Activity",
        "users",
        "View account activity for a user.",
    ),
    permission(
        "users.manage",
        "Manage Users",
        "users",
        "Perform general user-account administration.",
    ),
    permission(
        "roles.create",
        "Create Role",
        "roles",
        "Create a role.",
    ),
    permission(
        "roles.view",
        "View Role",
        "roles",
        "View role details.",
    ),
    permission(
        "roles.list",
        "List Roles",
        "roles",
        "List roles.",
    ),
    permission(
        "roles.update",
        "Update Role",
        "roles",
        "Update a role.",
    ),
    permission(
        "roles.delete",
        "Delete Role",
        "roles",
        "Delete a non-system role.",
    ),
    permission(
        "roles.assign_permission",
        "Assign Role Permission",
        "roles",
        "Assign a permission to a role.",
    ),
    permission(
        "roles.remove_permission",
        "Remove Role Permission",
        "roles",
        "Remove a permission from a role.",
    ),
    permission(
        "roles.manage",
        "Manage Roles",
        "roles",
        "Perform general role administration.",
    ),
    permission(
        "permissions.create",
        "Create Permission",
        "permissions",
        "Create a permission.",
    ),
    permission(
        "permissions.view",
        "View Permission",
        "permissions",
        "View permission details.",
    ),
    permission(
        "permissions.list",
        "List Permissions",
        "permissions",
        "List permissions.",
    ),
    permission(
        "permissions.update",
        "Update Permission",
        "permissions",
        "Update permission metadata.",
    ),
    permission(
        "permissions.delete",
        "Delete Permission",
        "permissions",
        "Delete a non-system permission.",
    ),
    permission(
        "permissions.manage",
        "Manage Permissions",
        "permissions",
        "Perform general permission administration.",
    ),
    permission(
        "audit_logs.view",
        "View Audit Log",
        "audit_logs",
        "View an audit-log record.",
    ),
    permission(
        "audit_logs.list",
        "List Audit Logs",
        "audit_logs",
        "List and filter audit-log records.",
    ),
    permission(
        "audit_logs.export",
        "Export Audit Logs",
        "audit_logs",
        "Export audit-log records.",
    ),
    permission(
        "user_activity.view",
        "View User Activity Log",
        "user_activity",
        "View user-activity records.",
    ),
)


WEEK_3_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "patient.create",
        "Create Patient",
        "patient",
        "Register a new patient.",
    ),
    permission(
        "patient.view",
        "View Patient",
        "patient",
        "View a patient profile.",
    ),
    permission(
        "patient.list",
        "List Patients",
        "patient",
        "List patients.",
    ),
    permission(
        "patient.search",
        "Search Patients",
        "patient",
        "Search for patients.",
    ),
    permission(
        "patient.update",
        "Update Patient",
        "patient",
        "Update patient demographic and profile information.",
    ),
    permission(
        "patient.activate",
        "Activate Patient",
        "patient",
        "Activate a patient record.",
    ),
    permission(
        "patient.deactivate",
        "Deactivate Patient",
        "patient",
        "Deactivate a patient record.",
    ),
    permission(
        "patient.archive",
        "Archive Patient",
        "patient",
        "Archive a patient record.",
    ),
    permission(
        "patient.restore",
        "Restore Patient",
        "patient",
        "Restore an archived patient record.",
    ),
    permission(
        "patient.view_sensitive_data",
        "View Sensitive Patient Data",
        "patient",
        "View protected patient fields permitted by policy.",
    ),
    permission(
        "patient.export",
        "Export Patient Data",
        "patient",
        "Export patient data.",
    ),
    permission(
        "patient_duplicate.check",
        "Check Patient Duplicates",
        "patient_duplicate",
        "Run duplicate-patient detection.",
    ),
    permission(
        "patient_duplicate.view_matches",
        "View Duplicate Matches",
        "patient_duplicate",
        "View possible duplicate-patient matches.",
    ),
    permission(
        "patient_duplicate.confirm_existing",
        "Confirm Existing Patient",
        "patient_duplicate",
        "Select an existing patient instead of creating a duplicate.",
    ),
    permission(
        "patient_duplicate.override",
        "Override Duplicate Warning",
        "patient_duplicate",
        (
            "Create a patient despite a duplicate warning with a "
            "mandatory reason."
        ),
    ),
    permission(
        "patient_duplicate.merge",
        "Merge Duplicate Patients",
        "patient_duplicate",
        "Merge verified duplicate patient records.",
    ),
    permission(
        "patient_duplicate.dismiss",
        "Dismiss Duplicate Match",
        "patient_duplicate",
        "Mark a possible duplicate as not matching.",
    ),
    permission(
        "patient_address.create",
        "Create Patient Address",
        "patient_address",
        "Add an address to a patient.",
    ),
    permission(
        "patient_address.view",
        "View Patient Address",
        "patient_address",
        "View a patient address.",
    ),
    permission(
        "patient_address.update",
        "Update Patient Address",
        "patient_address",
        "Update a patient address.",
    ),
    permission(
        "patient_address.delete",
        "Delete Patient Address",
        "patient_address",
        "Remove a patient address.",
    ),
    permission(
        "patient_identifier.create",
        "Create Patient Identifier",
        "patient_identifier",
        "Create a patient identifier.",
    ),
    permission(
        "patient_identifier.view",
        "View Patient Identifier",
        "patient_identifier",
        "View a patient identifier.",
    ),
    permission(
        "patient_identifier.update",
        "Update Patient Identifier",
        "patient_identifier",
        "Update a patient identifier.",
    ),
    permission(
        "patient_identifier.deactivate",
        "Deactivate Patient Identifier",
        "patient_identifier",
        "Deactivate an identifier while retaining history.",
    ),
    permission(
        "patient_document.upload",
        "Upload Patient Document",
        "patient_document",
        "Upload a patient document.",
    ),
    permission(
        "patient_document.view",
        "View Patient Document",
        "patient_document",
        "View patient-document metadata.",
    ),
    permission(
        "patient_document.download",
        "Download Patient Document",
        "patient_document",
        "Download a patient document.",
    ),
    permission(
        "patient_document.update",
        "Update Patient Document",
        "patient_document",
        "Update patient-document metadata.",
    ),
    permission(
        "patient_document.delete",
        "Delete Patient Document",
        "patient_document",
        "Soft-delete a patient document with an audit reason.",
    ),
    permission(
        "patient_document.verify",
        "Verify Patient Document",
        "patient_document",
        "Verify a patient document.",
    ),
)


WEEK_4_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "medical_history.create",
        "Create Medical History",
        "medical_history",
        "Create a medical-history record.",
    ),
    permission(
        "medical_history.view",
        "View Medical History",
        "medical_history",
        "View medical-history records.",
    ),
    permission(
        "medical_history.update",
        "Update Medical History",
        "medical_history",
        "Update a medical-history record.",
    ),
    permission(
        "medical_history.delete",
        "Delete Medical History",
        "medical_history",
        "Soft-delete a medical-history record with an audit reason.",
    ),
    permission(
        "medical_history.view_audit",
        "View Medical-History Audit",
        "medical_history",
        "View medical-history change events.",
    ),
    permission(
        "patient_condition.create",
        "Create Patient Condition",
        "patient_condition",
        "Record a previous or current patient condition.",
    ),
    permission(
        "patient_condition.view",
        "View Patient Condition",
        "patient_condition",
        "View patient conditions.",
    ),
    permission(
        "patient_condition.update",
        "Update Patient Condition",
        "patient_condition",
        "Update a patient condition.",
    ),
    permission(
        "patient_condition.resolve",
        "Resolve Patient Condition",
        "patient_condition",
        "Mark a patient condition as resolved.",
    ),
    permission(
        "patient_condition.delete",
        "Delete Patient Condition",
        "patient_condition",
        "Soft-delete a patient condition with an audit reason.",
    ),
    permission(
        "patient_surgery.create",
        "Create Surgery History",
        "patient_surgery",
        "Record a previous surgery.",
    ),
    permission(
        "patient_surgery.view",
        "View Surgery History",
        "patient_surgery",
        "View previous surgery records.",
    ),
    permission(
        "patient_surgery.update",
        "Update Surgery History",
        "patient_surgery",
        "Update a previous surgery record.",
    ),
    permission(
        "patient_surgery.delete",
        "Delete Surgery History",
        "patient_surgery",
        "Soft-delete a surgery record with an audit reason.",
    ),
    permission(
        "existing_medicine.create",
        "Create Existing Medicine",
        "existing_medicine",
        "Record a medicine the patient is already taking.",
    ),
    permission(
        "existing_medicine.view",
        "View Existing Medicine",
        "existing_medicine",
        "View medicines the patient is already taking.",
    ),
    permission(
        "existing_medicine.update",
        "Update Existing Medicine",
        "existing_medicine",
        "Update an existing-medicine record.",
    ),
    permission(
        "existing_medicine.stop",
        "Stop Existing Medicine",
        "existing_medicine",
        "Mark an existing medicine as stopped.",
    ),
    permission(
        "existing_medicine.delete",
        "Delete Existing Medicine",
        "existing_medicine",
        "Soft-delete an existing-medicine record with an audit reason.",
    ),
    permission(
        "allergy.create",
        "Create Allergy",
        "allergy",
        "Record a patient allergy.",
    ),
    permission(
        "allergy.view",
        "View Allergy",
        "allergy",
        "View patient allergies.",
    ),
    permission(
        "allergy.update",
        "Update Allergy",
        "allergy",
        "Update a patient allergy.",
    ),
    permission(
        "allergy.deactivate",
        "Deactivate Allergy",
        "allergy",
        "Deactivate an allergy while retaining history.",
    ),
    permission(
        "allergy.delete",
        "Delete Allergy",
        "allergy",
        "Soft-delete an allergy with an audit reason.",
    ),
    permission(
        "allergy.view_alert",
        "View Allergy Alert",
        "allergy",
        "View prominent allergy warnings.",
    ),
    permission(
        "allergy.acknowledge_alert",
        "Acknowledge Allergy Alert",
        "allergy",
        "Record that an allergy warning was reviewed.",
    ),
    permission(
        "emergency_contact.create",
        "Create Emergency Contact",
        "emergency_contact",
        "Add a patient emergency contact.",
    ),
    permission(
        "emergency_contact.view",
        "View Emergency Contact",
        "emergency_contact",
        "View patient emergency contacts.",
    ),
    permission(
        "emergency_contact.update",
        "Update Emergency Contact",
        "emergency_contact",
        "Update a patient emergency contact.",
    ),
    permission(
        "emergency_contact.delete",
        "Delete Emergency Contact",
        "emergency_contact",
        "Delete a patient emergency contact.",
    ),
    permission(
        "emergency_contact.set_primary",
        "Set Primary Emergency Contact",
        "emergency_contact",
        "Set the primary patient emergency contact.",
    ),
    permission(
        "emergency_contact.verify",
        "Verify Emergency Contact",
        "emergency_contact",
        "Verify a patient emergency contact.",
    ),
    permission(
        "consent_template.create",
        "Create Consent Template",
        "consent_template",
        "Create a consent-form template.",
    ),
    permission(
        "consent_template.view",
        "View Consent Template",
        "consent_template",
        "View a consent-form template.",
    ),
    permission(
        "consent_template.list",
        "List Consent Templates",
        "consent_template",
        "List consent-form templates.",
    ),
    permission(
        "consent_template.update",
        "Update Consent Template",
        "consent_template",
        "Update a consent-form template.",
    ),
    permission(
        "consent_template.activate",
        "Activate Consent Template",
        "consent_template",
        "Activate a consent-form template.",
    ),
    permission(
        "consent_template.deactivate",
        "Deactivate Consent Template",
        "consent_template",
        "Deactivate a consent-form template.",
    ),
    permission(
        "consent_template.delete",
        "Delete Consent Template",
        "consent_template",
        "Delete an unused consent-form template.",
    ),
    permission(
        "patient_consent.create",
        "Create Patient Consent",
        "patient_consent",
        "Create a patient-consent record.",
    ),
    permission(
        "patient_consent.view",
        "View Patient Consent",
        "patient_consent",
        "View a patient-consent record.",
    ),
    permission(
        "patient_consent.capture",
        "Capture Patient Consent",
        "patient_consent",
        "Capture digital patient consent and signature data.",
    ),
    permission(
        "patient_consent.upload",
        "Upload Patient Consent",
        "patient_consent",
        "Upload a signed consent document.",
    ),
    permission(
        "patient_consent.download",
        "Download Patient Consent",
        "patient_consent",
        "Download a patient-consent document.",
    ),
    permission(
        "patient_consent.revoke",
        "Revoke Patient Consent",
        "patient_consent",
        "Record patient-consent revocation without deleting history.",
    ),
    permission(
        "patient_consent.verify",
        "Verify Patient Consent",
        "patient_consent",
        "Verify a captured or uploaded consent.",
    ),
)


# =========================================================
# PATIENT BOOKING PERMISSIONS
# =========================================================

PATIENT_BOOKING_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "patient_booking.create",
        "Create Patient Booking",
        "patient_booking",
        "Create a patient booking for the authenticated patient or by authorized staff.",
    ),
    permission(
        "patient_booking.view",
        "View Patient Booking",
        "patient_booking",
        "View a patient booking. Patient routes must be restricted to the authenticated patient's own booking.",
    ),
    permission(
        "patient_booking.list",
        "List Patient Bookings",
        "patient_booking",
        "List patient bookings. Patient routes must return only the authenticated patient's own bookings.",
    ),
    permission(
        "patient_booking.reschedule",
        "Reschedule Patient Booking",
        "patient_booking",
        "Reschedule a patient booking to another available date and time.",
    ),
    permission(
        "patient_booking.cancel",
        "Cancel Patient Booking",
        "patient_booking",
        "Cancel an active patient booking.",
    ),
)


# =========================================================
# WEEK 5 - APPOINTMENT MANAGEMENT
# =========================================================

WEEK_5_PERMISSIONS: tuple[PermissionSeed, ...] = (
    *PATIENT_BOOKING_PERMISSIONS,
    permission(
        "appointments.view",
        "View Appointments",
        "appointments",
        "View and list appointments.",
    ),
    permission(
        "appointments.create",
        "Create Appointments",
        "appointments",
        "Create walk-in, online and follow-up appointments.",
    ),
    permission(
        "appointments.update",
        "Update Appointments",
        "appointments",
        "Update appointment details.",
    ),
    permission(
        "appointments.confirm",
        "Confirm Appointments",
        "appointments",
        "Confirm a pending appointment.",
    ),
    permission(
        "appointments.checkin",
        "Check In Patient",
        "appointments",
        "Check a patient in for an appointment.",
    ),
    permission(
        "appointments.consult",
        "Start Consultation",
        "appointments",
        "Start consultation for a checked-in appointment.",
    ),
    permission(
        "appointments.complete",
        "Complete Appointment",
        "appointments",
        "Mark an appointment consultation as completed.",
    ),
    permission(
        "appointments.reschedule",
        "Reschedule Appointment",
        "appointments",
        "Reschedule an existing appointment.",
    ),
    permission(
        "appointments.no_show",
        "Mark Appointment No Show",
        "appointments",
        "Mark a confirmed appointment as no-show.",
    ),
    permission(
        "appointment_slots.view",
        "View Appointment Slots",
        "appointment_slots",
        "View doctor appointment slots and available slots.",
    ),
    permission(
        "appointment_slots.manage",
        "Manage Appointment Slots",
        "appointment_slots",
        "Create, block and unblock appointment slots.",
    ),
    permission(
        "doctor_availability.view",
        "View Doctor Availability",
        "doctor_availability",
        "View doctor schedules and availability.",
    ),
    permission(
        "doctor_availability.manage",
        "Manage Doctor Availability",
        "doctor_availability",
        "Create, update and disable doctor availability.",
    ),
    permission(
        "doctor_availability.manage_own",
        "Manage Own Doctor Availability",
        "doctor_availability",
        "Manage the authenticated doctor's availability.",
    ),
    permission(
        "appointment_waiting_list.view",
        "View Appointment Waiting List",
        "appointment_waiting_list",
        "View patients waiting for appointment slots.",
    ),
    permission(
        "appointment_waiting_list.manage",
        "Manage Appointment Waiting List",
        "appointment_waiting_list",
        "Add and update appointment waiting-list entries.",
    ),
)


# =========================================================
# WEEK 6 - DUTY DOCTOR CONSULTATION
# =========================================================

WEEK_6_PERMISSIONS: tuple[PermissionSeed, ...] = (
    permission(
        "consultations.create",
        "Create Consultation",
        "consultations",
        "Start a patient consultation as an authorized duty doctor.",
    ),
    permission(
        "consultations.view_own",
        "View Own Consultations",
        "consultations",
        "View consultations assigned to or created by the authenticated duty doctor.",
    ),
    permission(
        "consultations.view_all",
        "View All Consultations",
        "consultations",
        "View all patient consultations. Intended for administrators and other explicitly authorized roles.",
    ),
    permission(
        "consultations.update",
        "Update Consultation",
        "consultations",
        "Update an active consultation, including medical assessment and clinical observations.",
    ),
    permission(
        "consultations.status",
        "Update Consultation Status",
        "consultations",
        "Change consultation status, including in-progress, referred, completed and cancelled states.",
    ),
    permission(
        "consultations.history",
        "View Consultation History",
        "consultations",
        "View a patient's previous consultation history.",
    ),
    permission(
        "patient_vitals.view",
        "View Patient Vitals",
        "patient_vitals",
        "View vital-sign records captured during a patient consultation.",
    ),
    permission(
        "patient_vitals.manage",
        "Manage Patient Vitals",
        "patient_vitals",
        "Create and update vital-sign records during an authorized patient consultation.",
    ),
    permission(
        "clinical_notes.view",
        "View Clinical Notes",
        "clinical_notes",
        "View initial clinical notes, assessment notes, observations and follow-up notes.",
    ),
    permission(
        "clinical_notes.manage",
        "Manage Clinical Notes",
        "clinical_notes",
        "Create and update clinical notes for an authorized patient consultation.",
    ),
    permission(
        "diagnoses.view",
        "View Diagnoses",
        "diagnoses",
        "View patient diagnoses recorded during consultations.",
    ),
    permission(
        "diagnoses.manage",
        "Manage Diagnoses",
        "diagnoses",
        "Record and update provisional, differential and final diagnoses.",
    ),
    permission(
        "specialist_referrals.view",
        "View Specialist Referrals",
        "specialist_referrals",
        "View specialist referrals associated with a patient consultation.",
    ),
    permission(
        "specialist_referrals.manage",
        "Manage Specialist Referrals",
        "specialist_referrals",
        "Create and update specialist referrals from an authorized consultation.",
    ),
    permission(
        "case_shares.view",
        "View Case Shares",
        "case_shares",
        "View clinical cases shared with authorized doctors or specialists.",
    ),
    permission(
        "case_shares.manage",
        "Manage Case Shares",
        "case_shares",
        "Share an authorized patient consultation with another doctor or specialist.",
    ),
)


# =========================================================
# WEEK 8 - SPECIALIST DOCTOR + TREATMENT PLAN ENGINE
# =========================================================

WEEK_8_PERMISSIONS: tuple[PermissionSeed, ...] = (
    # Specialist case review
    permission(
        "specialist_cases.view",
        "View Specialist Cases",
        "specialist_cases",
        "View patient cases assigned or shared with the specialist.",
    ),
    permission(
        "specialist_cases.history",
        "View Specialist Patient History",
        "specialist_cases",
        "View consultation history for patients under specialist review.",
    ),

    # Treatment plans
    permission(
        "treatment_plans.create",
        "Create Treatment Plan",
        "treatment_plans",
        "Create a new specialist treatment plan.",
    ),
    permission(
        "treatment_plans.view",
        "View Treatment Plan",
        "treatment_plans",
        "View an accessible treatment plan.",
    ),
    permission(
        "treatment_plans.view_own",
        "View Own Treatment Plans",
        "treatment_plans",
        "List treatment plans created by the authenticated specialist.",
    ),
    permission(
        "treatment_plans.update",
        "Update Treatment Plan",
        "treatment_plans",
        "Update an editable treatment plan.",
    ),
    permission(
        "treatment_plans.delete",
        "Delete Draft Treatment Plan",
        "treatment_plans",
        "Delete a treatment plan while it remains in DRAFT status.",
    ),
    permission(
        "treatment_plans.submit",
        "Submit Treatment Plan",
        "treatment_plans",
        "Submit a treatment plan for review.",
    ),
    permission(
        "treatment_plans.review",
        "Review Treatment Plan",
        "treatment_plans",
        "Review a submitted treatment plan and request modifications when needed.",
    ),
    permission(
        "treatment_plans.approve",
        "Approve Treatment Plan",
        "treatment_plans",
        "Approve a treatment plan after clinical review.",
    ),
    permission(
        "treatment_plans.finalize",
        "Finalize Treatment Plan",
        "treatment_plans",
        "Finalize an approved treatment plan and make it read-only.",
    ),
    permission(
        "treatment_plans.cancel",
        "Cancel Treatment Plan",
        "treatment_plans",
        "Cancel an eligible treatment plan with a reason.",
    ),

    # Treatment plan therapies
    permission(
        "treatment_plan_therapies.view",
        "View Treatment Plan Therapies",
        "treatment_plan_therapies",
        "View therapies attached to a treatment plan.",
    ),
    permission(
        "treatment_plan_therapies.manage",
        "Manage Treatment Plan Therapies",
        "treatment_plan_therapies",
        "Add, update and remove therapies from an editable treatment plan.",
    ),

    # Treatment plan medicines
    permission(
        "treatment_plan_medicines.view",
        "View Treatment Plan Medicines",
        "treatment_plan_medicines",
        "View medicine recommendations attached to a treatment plan.",
    ),
    permission(
        "treatment_plan_medicines.manage",
        "Manage Treatment Plan Medicines",
        "treatment_plan_medicines",
        "Add, update and remove medicine recommendations from an editable treatment plan.",
    ),

    # Treatment plan items / services
    permission(
        "treatment_plan_items.view",
        "View Treatment Plan Items",
        "treatment_plan_items",
        "View service, procedure and other items attached to a treatment plan.",
    ),
    permission(
        "treatment_plan_items.manage",
        "Manage Treatment Plan Items",
        "treatment_plan_items",
        "Add, update and remove service, procedure and other treatment-plan items.",
    ),

    # Multi-specialist collaboration
    permission(
        "treatment_plan_specialists.view",
        "View Treatment Plan Specialists",
        "treatment_plan_specialists",
        "View specialists collaborating on a treatment plan.",
    ),
    permission(
        "treatment_plan_specialists.manage",
        "Manage Treatment Plan Specialists",
        "treatment_plan_specialists",
        "Add or remove collaborating specialists from an editable treatment plan.",
    ),

    # Pricing
    permission(
        "treatment_plan_pricing.calculate",
        "Calculate Treatment Plan Pricing",
        "treatment_plan_pricing",
        "Calculate therapy, medicine, room and service pricing for a treatment plan.",
    ),

    # Version history
    permission(
        "treatment_plan_versions.view",
        "View Treatment Plan Versions",
        "treatment_plan_versions",
        "View immutable treatment-plan version history.",
    ),

    # Status history
    permission(
        "treatment_plan_status_history.view",
        "View Treatment Plan Status History",
        "treatment_plan_status_history",
        "View treatment-plan workflow status history.",
    ),
)


# Permissions assigned to the Patient role for the patient self-service portal.
#
# IMPORTANT:
# Use these permissions only with patient-owned routes, such as:
#   /api/v1/patient/medical-history
#   /api/v1/patient/clinical-records/conditions
#
# The backend route must derive the patient from the logged-in JWT. Do not use
# these permissions to allow a patient to access another patient's record.
PATIENT_ROLE_PERMISSION_CODES: tuple[str, ...] = (
    # Week 1: own account/profile
    "auth.login",
    "auth.logout",
    "auth.refresh_token",
    "auth.change_password",
    "auth.view_current_user",
    "profile.view_own",
    "profile.update_own",
    "session.view_own",
    "session.revoke_own",

    # Week 3: own patient profile and documents
    "patient.view",
    "patient.update",
    "patient_address.view",
    "patient_address.create",
    "patient_address.update",
    "patient_document.view",
    "patient_document.download",
    "patient_document.upload",
    "patient_document.update",

    # Week 4: medical history
    "medical_history.create",
    "medical_history.view",
    "medical_history.update",

    # Week 4: conditions
    "patient_condition.create",
    "patient_condition.view",
    "patient_condition.update",
    "patient_condition.resolve",

    # Week 4: surgeries
    "patient_surgery.create",
    "patient_surgery.view",
    "patient_surgery.update",

    # Week 4: existing medicines
    "existing_medicine.create",
    "existing_medicine.view",
    "existing_medicine.update",
    "existing_medicine.stop",

    # Week 4: allergies
    "allergy.create",
    "allergy.view",
    "allergy.update",
    "allergy.deactivate",
    "allergy.view_alert",

    # Week 4: emergency contacts
    "emergency_contact.create",
    "emergency_contact.view",
    "emergency_contact.update",
    "emergency_contact.set_primary",

    # Week 4: consent templates and patient consents
    "consent_template.view",
    "consent_template.list",
    "patient_consent.create",
    "patient_consent.view",
    "patient_consent.capture",
    "patient_consent.upload",
    "patient_consent.download",
    "patient_consent.revoke",

    # Patient Booking: own booking operations
    # IMPORTANT: these permissions must only be used on routes
    # that derive patient_id from the authenticated patient token.
    "patient_booking.create",
    "patient_booking.view",
    "patient_booking.list",
    "patient_booking.reschedule",
    "patient_booking.cancel",

    # Legacy/full appointment module permissions. Keep these only
    # while the older appointment module remains registered.
    "appointments.view",
    "appointments.create",
    "appointment_slots.view",
    "doctor_availability.view",

)

APPLICATION_PERMISSION_CODES = (
    "rbac.manage",
    "workflow.configure",
    "audit.view",
    "reports.view",
    "appointment.create",
    "appointment.manage",
    "billing.collect",
    "consent.manage",
    "consultation.create",
    "allergy.manage",
    "treatment_plan.create",
    "treatment_plan.update",
    "treatment_plan.prepare",
    "treatment_plan.review",
    "treatment_plan.approve",
    "treatment_plan.finalize",
    "pharmacy.dispense",
)

APPLICATION_PERMISSIONS: tuple[PermissionSeed, ...] = tuple(
    permission(
        code,
        code.replace("_", " ").replace(".", " ").title(),
        code.split(".", 1)[0],
        f"Allows {code}.",
    )
    for code in APPLICATION_PERMISSION_CODES
)


ALL_PERMISSIONS: tuple[PermissionSeed, ...] = (
    *WEEK_1_PERMISSIONS,
    *WEEK_2_PERMISSIONS,
    *WEEK_3_PERMISSIONS,
    *WEEK_4_PERMISSIONS,
    *WEEK_5_PERMISSIONS,
    *WEEK_6_PERMISSIONS,
    *WEEK_8_PERMISSIONS,
    *APPLICATION_PERMISSIONS,
)


def validate_permission_seeds() -> None:
    codes = [item.code for item in ALL_PERMISSIONS]

    duplicate_codes = {code for code in codes if codes.count(code) > 1}

    if duplicate_codes:
        raise ValueError(
            "Duplicate permission codes found: " f"{sorted(duplicate_codes)}"
        )


def _permission_values(
    seed: PermissionSeed,
) -> dict:
    """
    Return only values supported by the Permission model.

    Required model column:
    - code

    Supported optional columns:
    - name
    - module
    - description
    - is_active
    - is_system
    - is_system_permission
    """
    available_columns = {column.key for column in Permission.__table__.columns}

    values = {
        "code": seed.code,
        "name": seed.name,
        "module": seed.module,
        "action": seed.code.split(".", 1)[1] if "." in seed.code else seed.code,
        "description": seed.description,
        "is_active": True,
        "is_system": True,
        "is_system_permission": True,
    }

    return {
        key: value for key, value in values.items() if key in available_columns
    }


def _update_permission(
    permission_row: Permission,
    seed: PermissionSeed,
) -> None:
    available_columns = {column.key for column in Permission.__table__.columns}

    values = {
        "name": seed.name,
        "module": seed.module,
        "action": seed.code.split(".", 1)[1] if "." in seed.code else seed.code,
        "description": seed.description,
        "is_active": True,
        "is_system": True,
        "is_system_permission": True,
    }

    for key, value in values.items():
        if key in available_columns:
            setattr(
                permission_row,
                key,
                value,
            )


async def seed_permissions(
    db: AsyncSession,
) -> dict[str, int]:
    """
    Create or update all configured permissions, including Week 8.

    This function is idempotent:
    - existing permissions are matched using Permission.code;
    - existing rows are updated;
    - duplicate permission rows are not created.
    """
    validate_permission_seeds()

    created = 0
    updated = 0

    try:
        for seed in ALL_PERMISSIONS:
            result = await db.execute(
                select(Permission).where(Permission.code == seed.code)
            )
            existing_permission = result.scalar_one_or_none()

            if existing_permission is None:
                db.add(Permission(**_permission_values(seed)))
                created += 1
            else:
                _update_permission(
                    existing_permission,
                    seed,
                )
                updated += 1

        await db.commit()

        return {
            "created": created,
            "updated": updated,
            "total": len(ALL_PERMISSIONS),
        }

    except Exception:
        await db.rollback()
        raise


async def main() -> None:
    async with AsyncSessionLocal() as db:
        permission_result = await seed_permissions(db)

    await engine.dispose()

    logger.info(
        "Permission seed completed: %s",
        permission_result,
    )
    print(
        "Permission seed completed | "
        f"created={permission_result['created']} | "
        f"updated={permission_result['updated']} | "
        f"total={permission_result['total']}"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | " "%(name)s | %(message)s"),
    )
    asyncio.run(main())
