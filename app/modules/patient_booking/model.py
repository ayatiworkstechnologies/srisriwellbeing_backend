"""Backward-compatible model imports."""

from app.modules.patient_bookings.model import (
    PatientBooking,
    PatientBookingHistory,
)

__all__ = [
    "PatientBooking",
    "PatientBookingHistory",
]
