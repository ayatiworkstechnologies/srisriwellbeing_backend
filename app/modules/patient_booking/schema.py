"""Backward-compatible schema imports."""

from app.modules.patient_bookings.schema import (
    PatientBookingCreateRequest,
    PatientBookingHistoryResponse,
    PatientBookingRescheduleRequest,
    PatientBookingResponse,
    PatientDetailsResponse,
    StaffPatientBookingCreateRequest,
)

__all__ = [
    "PatientBookingCreateRequest",
    "PatientBookingHistoryResponse",
    "PatientBookingRescheduleRequest",
    "PatientBookingResponse",
    "PatientDetailsResponse",
    "StaffPatientBookingCreateRequest",
]
