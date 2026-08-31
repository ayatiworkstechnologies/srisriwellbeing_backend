from datetime import date, time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.main import app
from app.modules.appointments.enums import (
    AppointmentStatus,
    AppointmentType,
    BookingSource,
)
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import (
    AppointmentActionRequest,
    AppointmentCreateRequest,
    DoctorAvailabilityCreateRequest,
    DoctorAvailabilityUpdateRequest,
    PatientAppointmentCreateRequest,
)
from app.modules.appointments.service import AppointmentService
from app.modules.duty_doctor.repository import DutyDoctorRepository
from app.modules.duty_doctor.service import DutyDoctorService
from app.modules.patients.portal.appointments_router import (
    create_patient_appointment,
    ensure_patient_can_book,
    get_patient_appointment,
    list_patient_appointments,
)
from seeds.role_permissions_seed import (
    DUTY_DOCTOR_WEEK_5_PERMISSIONS,
    RECEPTIONIST_WEEK_5_PERMISSIONS,
)


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


def test_duty_doctor_can_manage_own_availability() -> None:
    assert (
        "doctor_availability.manage_own"
        in DUTY_DOCTOR_WEEK_5_PERMISSIONS
    )


def test_duty_doctor_cannot_manage_another_doctors_availability() -> None:
    with pytest.raises(HTTPException) as exc_info:
        AppointmentService._require_availability_owner(
            doctor_id=8,
            actor_id=7,
            can_manage_all=False,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_availability_update_rebuilds_future_unbooked_slots(
    monkeypatch,
) -> None:
    availability = SimpleNamespace(
        id=3,
        doctor_id=7,
        day_of_week=1,
        start_time=time(9),
        end_time=time(12),
        slot_duration_minutes=30,
        is_active=True,
    )
    stale_slot = SimpleNamespace(
        slot_date=date(2026, 9, 1),
    )
    db = SimpleNamespace(
        delete=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    monkeypatch.setattr(
        AppointmentRepository,
        "get_availability_by_id",
        AsyncMock(return_value=availability),
    )
    monkeypatch.setattr(
        AppointmentRepository,
        "get_future_unbooked_slots",
        AsyncMock(return_value=[stale_slot]),
    )

    result = await AppointmentService.update_doctor_availability(
        db=db,
        availability_id=3,
        payload=DoctorAvailabilityUpdateRequest(
            start_time=time(10),
        ),
        actor_id=7,
        can_manage_all=False,
    )

    assert result.start_time == time(10)
    db.delete.assert_awaited_once_with(stale_slot)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_duty_doctor_creates_own_availability(monkeypatch) -> None:
    db = SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
        rollback=AsyncMock(),
    )
    create_availability = AsyncMock()
    monkeypatch.setattr(
        AppointmentRepository,
        "get_duty_doctor_by_id",
        AsyncMock(return_value=SimpleNamespace(id=7)),
    )
    monkeypatch.setattr(
        AppointmentRepository,
        "create_availability",
        create_availability,
    )

    result = await AppointmentService.create_doctor_availability(
        db=db,
        payload=DoctorAvailabilityCreateRequest(
            doctor_id=7,
            day_of_week=1,
            start_time=time(9),
            end_time=time(12),
            slot_duration_minutes=30,
        ),
        actor_id=7,
        can_manage_all=False,
    )

    assert result.doctor_id == 7
    assert result.start_time == time(9)
    create_availability.assert_awaited_once()
    db.commit.assert_awaited_once()


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


def test_obsolete_patient_booking_routes_are_not_exposed() -> None:
    paths = {route.path for route in app.routes}

    assert not any("/patient-bookings" in path for path in paths)


@pytest.mark.asyncio
async def test_start_appointment_creates_linked_consultation(
    monkeypatch,
) -> None:
    appointment = SimpleNamespace(
        id=10,
        patient_id=42,
        doctor_id=7,
        status=AppointmentStatus.CHECKED_IN.value,
        consultation_started_at=None,
    )
    db = SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    monkeypatch.setattr(
        AppointmentRepository,
        "get_appointment",
        AsyncMock(return_value=appointment),
    )

    async def change_status(**kwargs):
        kwargs["appointment"].status = kwargs["new_status"]

    monkeypatch.setattr(
        AppointmentService,
        "_change_status",
        change_status,
    )
    monkeypatch.setattr(
        DutyDoctorRepository,
        "get_by_appointment",
        AsyncMock(return_value=None),
    )
    create_consultation = AsyncMock(return_value=SimpleNamespace(id=3))
    monkeypatch.setattr(
        DutyDoctorService,
        "create_consultation",
        create_consultation,
    )

    result = await AppointmentService.start_consultation(
        db=db,
        appointment_id=10,
        changed_by=7,
        payload=AppointmentActionRequest(),
    )

    assert result.status == AppointmentStatus.IN_CONSULTATION.value
    request = create_consultation.await_args.kwargs["data"]
    assert request.patient_id == 42
    assert request.appointment_id == 10
    assert create_consultation.await_args.kwargs["commit"] is False
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_appointment_is_idempotent_for_own_consultation(
    monkeypatch,
) -> None:
    started_at = object()
    appointment = SimpleNamespace(
        id=10,
        patient_id=42,
        doctor_id=7,
        status=AppointmentStatus.IN_CONSULTATION.value,
        consultation_started_at=started_at,
    )
    db = SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    monkeypatch.setattr(
        AppointmentRepository,
        "get_appointment",
        AsyncMock(return_value=appointment),
    )
    monkeypatch.setattr(
        DutyDoctorRepository,
        "get_by_appointment",
        AsyncMock(
            return_value=SimpleNamespace(duty_doctor_id=7),
        ),
    )
    change_status = AsyncMock()
    monkeypatch.setattr(
        AppointmentService,
        "_change_status",
        change_status,
    )

    result = await AppointmentService.start_consultation(
        db=db,
        appointment_id=10,
        changed_by=7,
        payload=AppointmentActionRequest(),
    )

    assert result is appointment
    assert appointment.consultation_started_at is started_at
    change_status.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_appointment_completes_linked_consultation(
    monkeypatch,
) -> None:
    appointment = SimpleNamespace(
        id=10,
        status=AppointmentStatus.IN_CONSULTATION.value,
        completed_at=None,
    )
    consultation = SimpleNamespace(
        id=3,
        duty_doctor_id=7,
        status="IN_PROGRESS",
    )
    db = SimpleNamespace(
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    monkeypatch.setattr(
        AppointmentRepository,
        "get_appointment",
        AsyncMock(return_value=appointment),
    )
    monkeypatch.setattr(
        DutyDoctorRepository,
        "get_by_appointment",
        AsyncMock(return_value=consultation),
    )

    async def change_status(**kwargs):
        kwargs["appointment"].status = kwargs["new_status"]

    monkeypatch.setattr(
        AppointmentService,
        "_change_status",
        change_status,
    )
    monkeypatch.setattr(
        "app.modules.duty_doctor.audit.create_clinical_audit",
        AsyncMock(),
    )

    await AppointmentService.complete_appointment(
        db=db,
        appointment_id=10,
        changed_by=7,
        payload=AppointmentActionRequest(),
    )

    assert appointment.status == AppointmentStatus.COMPLETED.value
    assert consultation.status == "COMPLETED"
    db.commit.assert_awaited_once()
