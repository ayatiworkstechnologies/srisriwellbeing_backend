from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.appointments.enums import AppointmentStatus
from app.modules.appointments.repository import AppointmentRepository
from app.modules.duty_doctor.schemas import ConsultationCreate
from app.modules.duty_doctor.router import (
    get_consultation_by_appointment,
)
from app.modules.duty_doctor.service import DutyDoctorService


@pytest.mark.asyncio
async def test_consultation_rejects_another_doctors_appointment(
    monkeypatch,
) -> None:
    db = SimpleNamespace(
        scalar=AsyncMock(return_value=42),
    )
    appointment = SimpleNamespace(
        id=10,
        patient_id=42,
        doctor_id=99,
        status=AppointmentStatus.CHECKED_IN.value,
    )
    monkeypatch.setattr(
        AppointmentRepository,
        "get_appointment",
        AsyncMock(return_value=appointment),
    )

    with pytest.raises(HTTPException) as exc_info:
        await DutyDoctorService.create_consultation(
            db=db,
            doctor_id=7,
            data=ConsultationCreate(
                patient_id=42,
                appointment_id=10,
            ),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_completed_consultation_is_terminal() -> None:
    consultation = SimpleNamespace(
        id=3,
        status="COMPLETED",
        appointment_id=10,
    )

    with pytest.raises(HTTPException) as exc_info:
        await DutyDoctorService.update_status(
            db=object(),
            consultation=consultation,
            doctor_id=7,
            new_status="IN_PROGRESS",
        )

    assert exc_info.value.status_code == 409


@pytest.mark.parametrize(
    "consultation_status",
    ["COMPLETED", "CANCELLED"],
)
def test_terminal_consultation_rejects_clinical_changes(
    consultation_status: str,
) -> None:
    consultation = SimpleNamespace(status=consultation_status)

    with pytest.raises(HTTPException) as exc_info:
        DutyDoctorService.require_active_consultation(consultation)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_get_consultation_by_appointment_uses_duty_doctor_field(
) -> None:
    consultation = SimpleNamespace(id=3)
    scalars = SimpleNamespace(first=lambda: consultation)
    result = SimpleNamespace(scalars=lambda: scalars)
    db = SimpleNamespace(execute=AsyncMock(return_value=result))

    response = await get_consultation_by_appointment(
        appointment_id=10,
        current_user=SimpleNamespace(id=7),
        db=db,
    )

    assert response is consultation
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_terminal_referral_status_is_immutable() -> None:
    referral = SimpleNamespace(
        id=4,
        status="COMPLETED",
    )

    with pytest.raises(HTTPException) as exc_info:
        await DutyDoctorService.update_referral_status(
            db=object(),
            referral=referral,
            doctor_id=7,
            new_status="ACCEPTED",
        )

    assert exc_info.value.status_code == 409
