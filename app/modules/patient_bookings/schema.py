from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# PATIENT CREATE OWN BOOKING
# =========================================================

class PatientBookingCreateRequest(BaseModel):
    booking_date: date
    start_time: time
    end_time: time

    reason: str | None = Field(
        default=None,
        max_length=1000,
    )


# =========================================================
# STAFF CREATE BOOKING
# =========================================================

class StaffPatientBookingCreateRequest(
    PatientBookingCreateRequest
):
    patient_id: int = Field(
        gt=0,
    )


# =========================================================
# RESCHEDULE
# =========================================================

class PatientBookingRescheduleRequest(BaseModel):
    booking_date: date
    start_time: time
    end_time: time


# =========================================================
# RESPONSE
# =========================================================

class PatientDetailsResponse(BaseModel):
    id: int
    patient_code: str | None = None
    name: str
    email: str | None = None
    mobile_number: str


class PatientBookingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    patient_id: int

    booking_date: date
    start_time: time
    end_time: time

    status: str
    reason: str | None = None

    reschedule_count: int

    created_at: datetime
    updated_at: datetime

    patient: PatientDetailsResponse


class PatientBookingHistoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    booking_id: int

    old_date: date
    old_start_time: time
    old_end_time: time

    new_date: date
    new_start_time: time
    new_end_time: time

    action: str
    created_at: datetime
