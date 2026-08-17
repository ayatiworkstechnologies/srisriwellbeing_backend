from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.main import app
from app.modules.appointments.enums import AppointmentType, BookingSource
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import (
    AppointmentCreateRequest,
    PatientAppointmentCreateRequest,
)
from app.modules.appointments.service import AppointmentService
from app.modules.patients.portal.appointments_router import (
    create_patient_appointment,
    ensure_patient_can_book,
    get_patient_appointment,
    list_patient_appointments,
)
from seeds.role_permissions_seed import RECEPTIONIST_WEEK_5_PERMISSIONS


def test_staff_and_patient_appointment_routes_are_registered() -> None:
    routes = {
        (method, route.path)
        for route in app.routes
        for method in (route.methods or set())
    }

    expected = {
        ("POST", "/api/appointments"),
        ("POST", "/api/v1/appointments"),
        ("POST", "/api/patient/appointments"),
        ("POST", "/api/v1/patient/appointments"),
        ("GET", "/api/patient/appointments"),
        ("GET", "/patient/appointments"),
        ("GET", "/api/patient/appointments/available-slots"),
    }

    assert expected <= routes


@pytest.mark.parametrize(
    "appointment_type",
    [AppointmentType.WALK_IN, AppointmentType.ONLINE],
)
def test_receptionist_can_submit_walk_in_and_online_types(
    appointment_type,
) -> None:
    payload = AppointmentCreateRequest(
        patient_id=2,
        doctor_id=5,
        slot_id=8,
        appointment_type=appointment_type,
    )

    assert payload.appointment_type is appointment_type
    assert payload.booking_source is BookingSource.RECEPTION
    assert "appointments.create" in RECEPTIONIST_WEEK_5_PERMISSIONS


@pytest.mark.asyncio
async def test_patient_booking_is_owned_and_forced_online(monkeypatch) -> None:
    created_appointment = SimpleNamespace(id=12)
    create = AsyncMock(return_value=created_appointment)
    db = object()
    monkeypatch.setattr(
        AppointmentService,
        "create_patient_appointment",
        create,
    )

    payload = PatientAppointmentCreateRequest(
        doctor_id=5,
        slot_id=8,
        reason="Follow-up question",
    )

    result = await create_patient_appointment(
        payload=payload,
        current_patient=SimpleNamespace(id=42, status="ACTIVE"),
        current_user=SimpleNamespace(id=7),
        db=db,
    )

    assert result["data"] is created_appointment
    create.assert_awaited_once_with(
        db=db,
        payload=payload,
        patient_id=42,
        created_by=7,
    )


def test_inactive_patient_cannot_book() -> None:
    with pytest.raises(HTTPException) as exc_info:
        ensure_patient_can_book(
            SimpleNamespace(id=42, status="INACTIVE")
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_patient_appointment_list_is_scoped_to_logged_in_patient(
    monkeypatch,
) -> None:
    list_appointments = AsyncMock(return_value=([], 0))
    db = object()
    monkeypatch.setattr(
        AppointmentRepository,
        "list_appointments",
        list_appointments,
    )

    await list_patient_appointments(
        current_patient=SimpleNamespace(id=42),
        page=2,
        limit=10,
        db=db,
    )

    list_appointments.assert_awaited_once_with(
        db=db,
        patient_id=42,
        page=2,
        limit=10,
    )


@pytest.mark.asyncio
async def test_patient_cannot_read_another_patients_appointment(
    monkeypatch,
) -> None:
    get_appointment = AsyncMock(
        return_value=SimpleNamespace(id=3, patient_id=99)
    )
    monkeypatch.setattr(
        AppointmentRepository,
        "get_appointment",
        get_appointment,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_patient_appointment(
            appointment_id=3,
            current_patient=SimpleNamespace(id=42),
            db=object(),
        )

    assert exc_info.value.status_code == 404
