from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.utils import now_local
from app.modules.patients.constants import PatientStatus

from app.modules.patient_bookings.model import (
    PatientBooking,
    PatientBookingHistory,
)
from app.modules.patient_bookings.repository import (
    PatientBookingRepository,
)
from app.modules.patient_bookings.schema import (
    PatientBookingCreateRequest,
    PatientBookingRescheduleRequest,
)


class PatientBookingService:

    # =====================================================
    # PATIENT NAME
    # =====================================================

    @staticmethod
    def patient_name(
        patient,
    ) -> str:

        parts = [
            patient.first_name,
            patient.middle_name,
            patient.last_name,
        ]

        return " ".join(
            str(part).strip()
            for part in parts
            if part
        )

    # =====================================================
    # SERIALIZE
    # =====================================================

    @classmethod
    async def serialize_booking(
        cls,
        db: AsyncSession,
        booking: PatientBooking,
    ) -> dict:

        patient = (
            await PatientBookingRepository.get_patient(
                db=db,
                patient_id=booking.patient_id,
            )
        )

        if patient is None:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

        return {
            "id": booking.id,
            "patient_id": booking.patient_id,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "reason": booking.reason,
            "reschedule_count": (
                booking.reschedule_count
            ),
            "created_at": booking.created_at,
            "updated_at": booking.updated_at,

            "patient": {
                "id": patient.id,
                "patient_code": (
                    patient.patient_code
                ),
                "name": cls.patient_name(
                    patient
                ),
                "email": patient.email,
                "mobile_number": (
                    patient.mobile_number
                ),
            },
        }

    # =====================================================
    # VALIDATE SLOT
    # =====================================================

    @staticmethod
    async def validate_slot(
        db: AsyncSession,
        *,
        booking_date,
        start_time,
        end_time,
        exclude_booking_id: int | None = None,
    ) -> None:

        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "start_time must be earlier "
                    "than end_time"
                ),
            )

        now = now_local()

        slot_datetime = datetime.combine(
            booking_date,
            start_time,
        )

        if slot_datetime <= now:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Booking date and time "
                    "must be in the future"
                ),
            )

        conflict = (
            await PatientBookingRepository.slot_conflict_exists(
                db=db,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                exclude_booking_id=(
                    exclude_booking_id
                ),
            )
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Selected date and time "
                    "is already booked"
                ),
            )

    # =====================================================
    # CREATE
    # =====================================================

    @classmethod
    async def create_booking(
        cls,
        db: AsyncSession,
        *,
        patient_id: int,
        payload: PatientBookingCreateRequest,
    ) -> PatientBooking:

        patient = (
            await PatientBookingRepository.get_patient(
                db=db,
                patient_id=patient_id,
            )
        )

        if patient is None:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

        if patient.status != PatientStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only active patients can create bookings",
            )

        await cls.validate_slot(
            db=db,
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        booking = PatientBooking(
            patient_id=patient_id,
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            reason=payload.reason,
            status="BOOKED",
            reschedule_count=0,
        )

        try:
            await PatientBookingRepository.create_booking(
                db=db,
                booking=booking,
            )

            await db.commit()
            await db.refresh(
                booking
            )

            return booking

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # GET OWN BOOKING
    # =====================================================

    @staticmethod
    async def get_patient_booking(
        db: AsyncSession,
        *,
        patient_id: int,
        booking_id: int,
    ) -> PatientBooking:

        booking = (
            await PatientBookingRepository.get_patient_booking(
                db=db,
                booking_id=booking_id,
                patient_id=patient_id,
            )
        )

        if booking is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        return booking

    # =====================================================
    # RESCHEDULE
    # =====================================================

    @classmethod
    async def reschedule_booking(
        cls,
        db: AsyncSession,
        *,
        booking: PatientBooking,
        payload: PatientBookingRescheduleRequest,
    ) -> PatientBooking:

        if booking.status == "CANCELLED":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cancelled booking cannot "
                    "be rescheduled"
                ),
            )

        if booking.status == "COMPLETED":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Completed booking cannot "
                    "be rescheduled"
                ),
            )

        await cls.validate_slot(
            db=db,
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            exclude_booking_id=booking.id,
        )

        history = PatientBookingHistory(
            booking_id=booking.id,

            old_date=booking.booking_date,
            old_start_time=booking.start_time,
            old_end_time=booking.end_time,

            new_date=payload.booking_date,
            new_start_time=payload.start_time,
            new_end_time=payload.end_time,

            action="RESCHEDULED",
        )

        try:
            await PatientBookingRepository.create_history(
                db=db,
                history=history,
            )

            booking.booking_date = (
                payload.booking_date
            )

            booking.start_time = (
                payload.start_time
            )

            booking.end_time = (
                payload.end_time
            )

            booking.status = "RESCHEDULED"

            booking.reschedule_count += 1

            await db.commit()

            await db.refresh(
                booking
            )

            return booking

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # CANCEL
    # =====================================================

    @staticmethod
    async def cancel_booking(
        db: AsyncSession,
        booking: PatientBooking,
    ) -> PatientBooking:

        if booking.status == "CANCELLED":
            raise HTTPException(
                status_code=409,
                detail="Booking already cancelled",
            )

        if booking.status == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Completed booking cannot be cancelled",
            )

        booking.status = "CANCELLED"

        try:
            await db.commit()

            await db.refresh(
                booking
            )

            return booking

        except Exception:
            await db.rollback()
            raise
