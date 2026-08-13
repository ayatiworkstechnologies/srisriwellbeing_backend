from __future__ import annotations

from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patient_bookings.model import (
    PatientBooking,
    PatientBookingHistory,
)
from app.modules.patients.models import Patient


ACTIVE_BOOKING_STATUSES = (
    "BOOKED",
    "RESCHEDULED",
)


class PatientBookingRepository:

    # =====================================================
    # GET PATIENT
    # =====================================================

    @staticmethod
    async def get_patient(
        db: AsyncSession,
        patient_id: int,
    ) -> Patient | None:

        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # GET BOOKING
    # =====================================================

    @staticmethod
    async def get_booking(
        db: AsyncSession,
        booking_id: int,
    ) -> PatientBooking | None:

        result = await db.execute(
            select(PatientBooking).where(
                PatientBooking.id == booking_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # GET PATIENT BOOKING
    # =====================================================

    @staticmethod
    async def get_patient_booking(
        db: AsyncSession,
        *,
        booking_id: int,
        patient_id: int,
    ) -> PatientBooking | None:

        result = await db.execute(
            select(PatientBooking).where(
                PatientBooking.id == booking_id,
                PatientBooking.patient_id == patient_id,
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # SLOT CONFLICT
    # =====================================================

    @staticmethod
    async def slot_conflict_exists(
        db: AsyncSession,
        *,
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: int | None = None,
    ) -> bool:

        query = select(
            PatientBooking.id
        ).where(
            PatientBooking.booking_date
            == booking_date,

            PatientBooking.status.in_(
                ACTIVE_BOOKING_STATUSES
            ),

            # Existing booking starts before
            # requested booking ends.
            PatientBooking.start_time
            < end_time,

            # Existing booking ends after
            # requested booking starts.
            PatientBooking.end_time
            > start_time,
        )

        if exclude_booking_id is not None:
            query = query.where(
                PatientBooking.id
                != exclude_booking_id
            )

        result = await db.execute(
            query.limit(1)
        )

        return result.scalar_one_or_none() is not None

    # =====================================================
    # CREATE
    # =====================================================

    @staticmethod
    async def create_booking(
        db: AsyncSession,
        booking: PatientBooking,
    ) -> PatientBooking:

        db.add(
            booking
        )

        await db.flush()

        return booking

    # =====================================================
    # LIST PATIENT BOOKINGS
    # =====================================================

    @staticmethod
    async def list_patient_bookings(
        db: AsyncSession,
        patient_id: int,
    ) -> list[PatientBooking]:

        result = await db.execute(
            select(PatientBooking)
            .where(
                PatientBooking.patient_id
                == patient_id
            )
            .order_by(
                PatientBooking.booking_date.desc(),
                PatientBooking.start_time.desc(),
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # LIST ALL
    # =====================================================

    @staticmethod
    async def list_all(
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PatientBooking]:

        result = await db.execute(
            select(PatientBooking)
            .order_by(
                PatientBooking.booking_date.desc(),
                PatientBooking.start_time.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # CREATE HISTORY
    # =====================================================

    @staticmethod
    async def create_history(
        db: AsyncSession,
        history: PatientBookingHistory,
    ) -> PatientBookingHistory:

        db.add(
            history
        )

        await db.flush()

        return history

    # =====================================================
    # HISTORY LIST
    # =====================================================

    @staticmethod
    async def get_history(
        db: AsyncSession,
        booking_id: int,
    ) -> list[PatientBookingHistory]:

        result = await db.execute(
            select(
                PatientBookingHistory
            )
            .where(
                PatientBookingHistory.booking_id
                == booking_id
            )
            .order_by(
                PatientBookingHistory.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )
