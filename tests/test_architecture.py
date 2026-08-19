import runpy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.models.base import Base
from app.modules.clinical.schemas import AllergyCreate
from app.modules.rbac.service import RBACService


def test_canonical_health_and_auth_routes_are_versioned() -> None:
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/health/ready" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/health/ready" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/forgot-password" in paths
    assert "/api/v1/auth/reset-password" in paths
    assert "/api/v1/auth/change-password" in paths
    assert "/api/v1/auth/me" in paths


def test_required_week_one_and_four_tables_are_registered() -> None:
    expected = {
        "users",
        "user_sessions",
        "refresh_tokens",
        "password_reset_tokens",
        "login_attempts",
        "audit_logs",
        "patient_medical_histories",
        "patient_conditions",
        "patient_surgeries",
        "patient_existing_medicines",
        "patient_allergies",
        "patient_emergency_contacts",
        "consent_templates",
        "patient_consents",
    }
    assert expected <= set(Base.metadata.tables)


def test_initial_migration_excludes_later_feature_tables() -> None:
    migration = runpy.run_path(
        Path("alembic/versions/20260804_0001_initial_schema.py")
    )
    initial_tables = migration["INITIAL_TABLE_NAMES"]

    assert "appointments" not in initial_tables
    assert "patient_bookings" not in initial_tables
    assert "consultations" not in initial_tables


def test_admin_is_not_a_clinical_authority_role() -> None:
    assert "admin" not in RBACService.CLINICAL_AUTHORITY_ROLES
    assert RBACService.CLINICAL_AUTHORITY_ROLES == {
        "duty_doctor",
        "specialist_doctor",
    }


def test_clinical_routes_are_versioned() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/patients/{patient_id}/clinical-summary" in paths
    assert "/api/v1/patients/{patient_id}/admission-readiness" in paths
    assert "/api/v1/patients/{patient_id}/allergies" in paths
    assert "/api/v1/patients/{patient_id}/emergency-contacts" in paths
    assert "/api/v1/patients/{patient_id}/consents" in paths
    assert "/api/v1/patients/consent-templates" in paths


def test_allergies_restrict_type_and_severity() -> None:
    allergy = AllergyCreate(
        allergy_type="drug",
        allergen="Penicillin",
        severity="severe",
    )
    assert allergy.is_active is True

    with pytest.raises(ValidationError):
        AllergyCreate(
            allergy_type="unknown",
            allergen="Dust",
            severity="critical",
        )
