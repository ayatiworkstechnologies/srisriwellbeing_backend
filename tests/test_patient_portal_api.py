from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.clinical.schemas import AllergyCreate, MedicalHistoryUpsert
from app.modules.clinical.service import ClinicalService
from app.modules.patients.portal.dashboard_router import (
    create_patient_allergy,
    delete_patient_clinical_resource,
    get_patient_clinical_summary,
    list_patient_clinical_resource,
    revoke_patient_consent,
    update_patient_clinical_resource,
    update_patient_medical_history,
)
from app.modules.patients.portal.schemas import PatientRegisterRequest


def test_patient_frontend_api_routes_are_registered() -> None:
    routes = {
        (method, route.path)
        for route in app.routes
        for method in (route.methods or set())
    }

    expected_routes = {
        ("POST", "/api/patient-auth/register"),
        ("POST", "/api/patient-auth/login"),
        ("POST", "/api/patient-auth/logout"),
        ("GET", "/api/patient/dashboard"),
        ("GET", "/api/patient/profile"),
        ("PATCH", "/api/patient/profile"),
        ("PUT", "/api/patient/medical-history"),
        ("GET", "/api/patient/clinical-summary"),
        ("GET", "/api/patient/admission-readiness"),
        ("GET", "/api/patient/clinical-records/{resource}"),
        ("POST", "/api/patient/clinical-records/allergies"),
        ("PATCH", "/api/patient/clinical-records/{resource}/{item_id}"),
        ("DELETE", "/api/patient/clinical-records/{resource}/{item_id}"),
        ("POST", "/api/patient/consents/{consent_id}/revoke"),
        ("GET", "/api/patient/consent-templates"),
        ("GET", "/api/patient/documents"),
        ("POST", "/api/patient/documents"),
        ("DELETE", "/api/patient/documents/{document_id}"),
        ("GET", "/api/patient/documents/{document_id}/download"),
    }

    assert expected_routes <= routes


def test_patient_routes_have_non_api_compatibility_aliases() -> None:
    routes = {
        (method, route.path)
        for route in app.routes
        for method in (route.methods or set())
    }

    expected_aliases = {
        ("POST", "/patient-auth/register"),
        ("POST", "/patient-auth/login"),
        ("POST", "/patient-auth/logout"),
        ("GET", "/patient/dashboard"),
        ("GET", "/patient/profile"),
        ("PATCH", "/patient/profile"),
        ("PUT", "/patient/medical-history"),
        ("GET", "/patient/documents"),
        ("GET", "/patient/clinical-summary"),
        ("GET", "/patient/admission-readiness"),
        ("GET", "/patient/clinical-records/{resource}"),
        ("POST", "/patient/clinical-records/allergies"),
        ("PATCH", "/patient/clinical-records/{resource}/{item_id}"),
        ("DELETE", "/patient/clinical-records/{resource}/{item_id}"),
        ("POST", "/patient/consents/{consent_id}/revoke"),
        ("GET", "/patient/consent-templates"),
        ("POST", "/patient/documents"),
        ("DELETE", "/patient/documents/{document_id}"),
        ("GET", "/patient/documents/{document_id}/download"),
    }
    assert expected_aliases <= routes


@pytest.mark.asyncio
async def test_patient_medical_history_uses_authenticated_patient_id(
    monkeypatch,
) -> None:
    payload = MedicalHistoryUpsert(previous_illnesses="Asthma")

    db = object()
    patient = SimpleNamespace(id=42)
    user = SimpleNamespace(id=7)
    upsert_history = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(ClinicalService, "upsert_history", upsert_history)

    result = await update_patient_medical_history(
        payload=payload,
        current_patient=patient,
        current_user=user,
        db=db,
    )

    assert result == {"success": True}
    upsert_history.assert_awaited_once_with(
        db=db,
        patient_id=42,
        data=payload.model_dump(),
        user_id=7,
    )


@pytest.mark.asyncio
async def test_patient_clinical_reads_use_authenticated_patient_id(
    monkeypatch,
) -> None:
    db = object()
    patient = SimpleNamespace(id=42)
    clinical_summary = AsyncMock(return_value={"success": True})
    list_resource = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(
        ClinicalService,
        "clinical_summary",
        clinical_summary,
    )
    monkeypatch.setattr(
        ClinicalService,
        "list_resource",
        list_resource,
    )

    await get_patient_clinical_summary(
        current_patient=patient,
        db=db,
    )
    await list_patient_clinical_resource(
        current_patient=patient,
        resource="allergies",
        db=db,
    )

    clinical_summary.assert_awaited_once_with(
        db=db,
        patient_id=42,
    )
    list_resource.assert_awaited_once_with(
        db=db,
        patient_id=42,
        resource="allergies",
    )


@pytest.mark.asyncio
async def test_patient_clinical_writes_use_authenticated_patient_id(
    monkeypatch,
) -> None:
    db = object()
    patient = SimpleNamespace(id=42)
    user = SimpleNamespace(id=7)
    payload = AllergyCreate(
        allergy_type="drug",
        allergen="Penicillin",
        severity="severe",
    )
    create_resource = AsyncMock(return_value={"success": True})
    update_resource = AsyncMock(return_value={"success": True})
    delete_resource = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(
        ClinicalService,
        "create_resource",
        create_resource,
    )
    monkeypatch.setattr(
        ClinicalService,
        "update_resource",
        update_resource,
    )
    monkeypatch.setattr(
        ClinicalService,
        "delete_resource",
        delete_resource,
    )

    await create_patient_allergy(
        payload=payload,
        current_patient=patient,
        current_user=user,
        db=db,
    )
    await update_patient_clinical_resource(
        payload={"is_active": False},
        current_patient=patient,
        current_user=user,
        resource="allergies",
        item_id=9,
        db=db,
    )
    await delete_patient_clinical_resource(
        current_patient=patient,
        current_user=user,
        resource="allergies",
        item_id=9,
        db=db,
    )

    create_resource.assert_awaited_once_with(
        db=db,
        patient_id=42,
        resource="allergies",
        data=payload.model_dump(),
        user_id=7,
    )
    update_resource.assert_awaited_once_with(
        db=db,
        patient_id=42,
        resource="allergies",
        item_id=9,
        data={"is_active": False},
        user_id=7,
    )
    delete_resource.assert_awaited_once_with(
        db=db,
        patient_id=42,
        resource="allergies",
        item_id=9,
        user_id=7,
    )


@pytest.mark.asyncio
async def test_patient_consent_revoke_uses_authenticated_patient_id(
    monkeypatch,
) -> None:
    db = object()
    patient = SimpleNamespace(id=42)
    revoke_consent = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(
        ClinicalService,
        "revoke_consent",
        revoke_consent,
    )

    await revoke_patient_consent(
        current_patient=patient,
        consent_id=12,
        db=db,
    )

    revoke_consent.assert_awaited_once_with(
        db=db,
        patient_id=42,
        consent_id=12,
    )


def test_patient_register_request_normalizes_input() -> None:
    payload = PatientRegisterRequest(
        full_name="  Test   Patient  ",
        email="PATIENT@EXAMPLE.COM",
        phone="+91 98765-43210",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
    )

    assert payload.full_name == "Test Patient"
    assert payload.email == "patient@example.com"
    assert payload.phone == "+919876543210"


def test_patient_register_accepts_frontend_camel_case_fields() -> None:
    payload = PatientRegisterRequest.model_validate(
        {
            "fullName": "Test Patient",
            "email": "patient@example.com",
            "mobileNumber": "9876543210",
            "password": "StrongPass1!",
            "confirmPassword": "StrongPass1!",
        }
    )

    assert payload.full_name == "Test Patient"
    assert payload.phone == "9876543210"
    assert payload.confirm_password == "StrongPass1!"


def test_patient_register_requires_matching_passwords() -> None:
    with pytest.raises(ValidationError):
        PatientRegisterRequest(
            full_name="Test Patient",
            email="patient@example.com",
            phone="9876543210",
            password="StrongPass1!",
            confirm_password="DifferentPass1!",
        )
