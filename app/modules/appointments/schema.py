from datetime import date, datetime, time

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.appointments.enums import (
    AppointmentType,
    BookingSource,
    WaitingListStatus,
)


# =========================================================
# DOCTOR AVAILABILITY - CREATE
# =========================================================


class DoctorAvailabilityCreateRequest(BaseModel):
    doctor_id: int

    day_of_week: int = Field(
        ge=0,
        le=6,
    )

    start_time: time
    end_time: time

    slot_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=240,
    )

    is_active: bool = True


# =========================================================
# DOCTOR AVAILABILITY - UPDATE
# =========================================================


class DoctorAvailabilityUpdateRequest(BaseModel):
    day_of_week: int | None = Field(
        default=None,
        ge=0,
        le=6,
    )

    start_time: time | None = None

    end_time: time | None = None

    slot_duration_minutes: int | None = Field(
        default=None,
        ge=5,
        le=240,
    )

    is_active: bool | None = None


# =========================================================
# DOCTOR AVAILABILITY - RESPONSE
# =========================================================


class DoctorAvailabilityResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    doctor_id: int

    day_of_week: int

    start_time: time
    end_time: time

    slot_duration_minutes: int

    is_active: bool


# =========================================================
# APPOINTMENT SLOT
# =========================================================


class AppointmentSlotResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    doctor_id: int

    slot_date: date

    start_time: time
    end_time: time

    is_available: bool
    is_blocked: bool

    appointment_id: int | None = None


class AvailableSlotResponse(AppointmentSlotResponse):
    """Available slot with an explicit booking identifier."""

    slot_id: int


class AvailableSlotsResponse(BaseModel):
    success: bool
    message: str
    data: list[AvailableSlotResponse]


# =========================================================
# BLOCK / UNBLOCK SLOT
# =========================================================


class SlotBlockRequest(BaseModel):
    is_blocked: bool


# =========================================================
# CREATE APPOINTMENT
# =========================================================


class AppointmentCreateRequest(BaseModel):
    patient_id: int

    doctor_id: int

    slot_id: int

    appointment_type: AppointmentType

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    booking_source: BookingSource = (
        BookingSource.RECEPTION
    )


class PatientAppointmentCreateRequest(BaseModel):
    """Input accepted when a logged-in patient books online."""

    # The slot is the source of truth for the doctor. doctor_id remains
    # optional for compatibility with clients that already submit it.
    doctor_id: int | None = Field(default=None, gt=0)
    slot_id: int = Field(gt=0)

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# UPDATE APPOINTMENT
# =========================================================


class AppointmentUpdateRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# APPOINTMENT RESPONSE
# =========================================================


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    appointment_number: str

    patient_id: int

    doctor_id: int

    slot_id: int | None

    appointment_type: str

    appointment_date: date

    start_time: time

    end_time: time

    reason: str | None

    notes: str | None

    status: str

    booking_source: str

    created_by: int | None

    parent_appointment_id: int | None

    rescheduled_from_id: int | None

    checked_in_at: datetime | None

    consultation_started_at: datetime | None

    completed_at: datetime | None

    no_show_at: datetime | None


# =========================================================
# APPOINTMENT ACTION
#
# Used for:
# confirm
# check-in
# consultation
# complete
# no-show
# =========================================================


class AppointmentActionRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# RESCHEDULE APPOINTMENT
# =========================================================


class AppointmentRescheduleRequest(BaseModel):
    slot_id: int

    reason: str = Field(
        min_length=2,
        max_length=2000,
    )


# =========================================================
# FOLLOW-UP APPOINTMENT
# =========================================================


class FollowUpAppointmentRequest(BaseModel):
    slot_id: int

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# APPOINTMENT STATUS HISTORY
# =========================================================


class AppointmentStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    appointment_id: int

    old_status: str | None

    new_status: str

    changed_by: int | None

    reason: str | None

    notes: str | None


# =========================================================
# WAITING LIST - CREATE
# =========================================================


class WaitingListCreateRequest(BaseModel):
    patient_id: int

    doctor_id: int

    preferred_date: date

    preferred_start_time: time | None = None

    preferred_end_time: time | None = None

    priority: int = Field(
        default=0,
        ge=0,
        le=10,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# WAITING LIST - UPDATE
# =========================================================


class WaitingListUpdateRequest(BaseModel):
    status: WaitingListStatus

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )


# =========================================================
# WAITING LIST - RESPONSE
# =========================================================


class WaitingListResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    patient_id: int

    doctor_id: int

    preferred_date: date

    preferred_start_time: time | None

    preferred_end_time: time | None

    priority: int

    status: str

    notes: str | None


# =========================================================
# APPOINTMENT CALENDAR RESPONSE
# =========================================================


class AppointmentCalendarResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    appointment_number: str

    patient_id: int

    doctor_id: int

    appointment_date: date

    start_time: time

    end_time: time

    appointment_type: str

    status: str


class ReceptionPatientStatusResponse(BaseModel):
    patient_id: int
    appointment_date: date

    has_active_appointment: bool

    appointment_id: int | None = None
    doctor_id: int | None = None
    status: str | None = None

    start_time: time | None = None
    end_time: time | None = None


class DutyDoctorOptionResponse(BaseModel):
    id: int
    full_name: str
    email: str | None = None


class AvailableSlotResponse(BaseModel):
    id: int
    doctor_id: int

    slot_date: date

    start_time: time
    end_time: time

    is_available: bool


class DoctorBookingAvailabilityResponse(BaseModel):
    doctor_id: int
    appointment_date: date

    available_now: bool

    available_slots: list[
        AvailableSlotResponse
    ]


class AppointmentActionResponse(BaseModel):
    success: bool
    message: str

    appointment_id: int
    status: str
