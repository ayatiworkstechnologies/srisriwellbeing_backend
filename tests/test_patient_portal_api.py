import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.patients.portal.schemas import (
    PatientRegisterRequest,
)


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
        ("GET", "/api/patient/documents"),
        ("POST", "/api/patient/documents"),
        ("DELETE", "/api/patient/documents/{document_id}"),
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
        ("GET", "/patient/documents"),
        ("POST", "/patient/documents"),
        ("DELETE", "/patient/documents/{document_id}"),
    }

    assert expected_aliases <= routes


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
