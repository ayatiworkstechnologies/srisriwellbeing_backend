"""Compatibility imports for the patient booking module.

The canonical implementation lives in ``app.modules.patient_bookings``.
This package preserves the older singular import path.
"""

from app.modules.patient_bookings.model import (
    PatientBooking,
    PatientBookingHistory,
)

__all__ = [
    "PatientBooking",
    "PatientBookingHistory",
]
