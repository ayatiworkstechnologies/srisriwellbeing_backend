"""Backward-compatible repository imports."""

from app.modules.patient_bookings.repository import (
    ACTIVE_BOOKING_STATUSES,
    PatientBookingRepository,
)

__all__ = [
    "ACTIVE_BOOKING_STATUSES",
    "PatientBookingRepository",
]
