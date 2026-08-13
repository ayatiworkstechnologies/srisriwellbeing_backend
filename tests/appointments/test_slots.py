from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.appointments.service import AppointmentService
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
