from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


# =========================================================
# DOCTOR AVAILABILITY
# =========================================================


class DoctorAvailability(BaseModel):
    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Python weekday:
    # Monday    = 0
    # Tuesday   = 1
    # Wednesday = 2
    # Thursday  = 3
    # Friday    = 4
    # Saturday  = 5
    # Sunday    = 6
    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "day_of_week",
            "start_time",
            "end_time",
            name="uq_doctor_availability_period",
        ),
        Index(
            "ix_doctor_availability_lookup",
            "doctor_id",
            "day_of_week",
            "is_active",
        ),
    )


# =========================================================
# APPOINTMENT SLOTS
# =========================================================


class AppointmentSlot(BaseModel):
    __tablename__ = "appointment_slots"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    slot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # This points back to appointments.
    # use_alter helps Alembic/MySQL handle the circular FK:
    #
    # appointments.slot_id
    #          ↕
    # appointment_slots.appointment_id
    appointment_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointments.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_appointment_slots_appointment_id",
        ),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "slot_date",
            "start_time",
            name="uq_doctor_slot",
        ),
        Index(
            "ix_appointment_slot_lookup",
            "doctor_id",
            "slot_date",
            "is_available",
            "is_blocked",
        ),
    )


# =========================================================
# APPOINTMENTS
# =========================================================


class Appointment(BaseModel):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    appointment_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "patients.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    slot_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointment_slots.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # WALK_IN
    # ONLINE
    # FOLLOW_UP
    appointment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    appointment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # PENDING
    # CONFIRMED
    # CHECKED_IN
    # IN_CONSULTATION
    # COMPLETED
    # RESCHEDULED
    # NO_SHOW
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    # ADMIN
    # RECEPTION
    # PATIENT_PORTAL
    # DOCTOR
    booking_source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RECEPTION",
        index=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # Used for follow-up appointments.
    #
    # Original appointment
    #       ↓
    # Follow-up appointment
    parent_appointment_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # Used when an appointment is rescheduled.
    #
    # Old appointment
    #       ↓
    # New appointment
    rescheduled_from_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    consultation_started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    no_show_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_appointments_doctor_date",
            "doctor_id",
            "appointment_date",
        ),
        Index(
            "ix_appointments_patient_date",
            "patient_id",
            "appointment_date",
        ),
        Index(
            "ix_appointments_status_date",
            "status",
            "appointment_date",
        ),
    )


# =========================================================
# APPOINTMENT STATUS HISTORY
# =========================================================


class AppointmentStatusHistory(BaseModel):
    __tablename__ = "appointment_status_history"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    appointment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    old_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    new_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    changed_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_appointment_history_appointment_status",
            "appointment_id",
            "new_status",
        ),
    )


# =========================================================
# APPOINTMENT WAITING LIST
# =========================================================


class AppointmentWaitingList(BaseModel):
    __tablename__ = "appointment_waiting_list"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    preferred_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    preferred_start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    preferred_end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # WAITING
    # SLOT_OFFERED
    # BOOKED
    # EXPIRED
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="WAITING",
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_waiting_list_doctor_date_status",
            "doctor_id",
            "preferred_date",
            "status",
        ),
    )


# =========================================================
# APPOINTMENT REMINDERS
# =========================================================


class AppointmentReminder(BaseModel):
    __tablename__ = "appointment_reminders"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    appointment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "appointments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Examples:
    # APPOINTMENT_24_HOURS
    # APPOINTMENT_2_HOURS
    reminder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # PENDING
    # SENT
    # FAILED
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    # SMS
    # EMAIL
    # WHATSAPP
    # PUSH
    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_appointment_reminder_schedule",
            "status",
            "scheduled_at",
        ),
    )
