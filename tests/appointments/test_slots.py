from datetime import date, time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.appointments.service import AppointmentService
from app.modules.appointments.router import get_available_slots
from app.modules.patients.portal.appointments_router import (
    get_patient_available_slots,
)


@pytest.mark.asyncio
async def test_patient_can_view_online_booking_slots(monkeypatch) -> None:
    slot_date = date(2030, 1, 2)
    slots = [SimpleNamespace(id=1)]
    db = object()
    get_slots = AsyncMock(return_value=slots)
    monkeypatch.setattr(AppointmentService, "get_available_slots", get_slots)

    response = await get_patient_available_slots(
        current_patient=SimpleNamespace(id=42, status="ACTIVE"),
        doctor_id=5,
        appointment_date=slot_date,
        db=db,
    )

    assert response["data"] == slots
    get_slots.assert_awaited_once_with(
        db=db,
        doctor_id=5,
        slot_date=slot_date,
    )


@pytest.mark.asyncio
async def test_staff_slot_response_exposes_slot_id(monkeypatch) -> None:
    slot = SimpleNamespace(
        id=12,
        doctor_id=9,
        slot_date=date(2026, 8, 20),
        start_time=time(9, 0),
        end_time=time(9, 30),
        is_available=True,
        is_blocked=False,
        appointment_id=None,
    )
    monkeypatch.setattr(
        AppointmentService,
        "get_available_slots",
        AsyncMock(return_value=[slot]),
    )

    response = await get_available_slots(
        doctor_id=9,
        appointment_date=date(2026, 8, 20),
        db=object(),
        current_user=SimpleNamespace(id=2),
    )

    assert response["data"][0]["id"] == 12
    assert response["data"][0]["slot_id"] == 12
