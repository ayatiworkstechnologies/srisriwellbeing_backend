from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PatientBooking(Base):
    __tablename__ = "patient_bookings"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # patients.id is INTEGER in your existing project.
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    booking_date: Mapped[date] = mapped_column(
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

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="BOOKED",
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reschedule_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_patient_bookings_date_time",
            "booking_date",
            "start_time",
            "end_time",
        ),
    )


class PatientBookingHistory(Base):
    __tablename__ = "patient_booking_history"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    booking_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "patient_bookings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    old_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    old_start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    old_end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    new_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    new_start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    new_end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RESCHEDULED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )