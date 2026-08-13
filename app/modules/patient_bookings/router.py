from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission

from app.modules.patient_bookings.repository import (
    PatientBookingRepository,
)
from app.modules.patient_bookings.schema import (
    PatientBookingCreateRequest,
    PatientBookingRescheduleRequest,
    StaffPatientBookingCreateRequest,
)
from app.modules.patient_bookings.service import (
    PatientBookingService,
)

from app.modules.patients.models import Patient

from app.modules.patients.portal.dependencies import (
    get_current_patient,
)

from app.modules.users.model import User


router = APIRouter(
    prefix="/patient-bookings",
    tags=["Patient Bookings"],
)


# =========================================================
# PATIENT - CREATE OWN BOOKING
# =========================================================

@router.post(
    "/my",
    status_code=status.HTTP_201_CREATED,
)
async def create_my_booking(
    payload: PatientBookingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(
        get_current_patient
    ),
) -> dict:

    booking = (
        await PatientBookingService.create_booking(
            db=db,
            patient_id=current_patient.id,
            payload=payload,
        )
    )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking created successfully",
        "data": data,
    }


# =========================================================
# PATIENT - LIST OWN BOOKINGS
# =========================================================

@router.get(
    "/my",
)
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(
        get_current_patient
    ),
) -> dict:

    bookings = (
        await PatientBookingRepository.list_patient_bookings(
            db=db,
            patient_id=current_patient.id,
        )
    )

    data = []

    for booking in bookings:
        data.append(
            await PatientBookingService.serialize_booking(
                db=db,
                booking=booking,
            )
        )

    return {
        "success": True,
        "message": "Bookings retrieved successfully",
        "data": data,
    }


# =========================================================
# PATIENT - GET OWN BOOKING
# =========================================================

@router.get(
    "/my/{booking_id}",
)
async def get_my_booking(
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(
        get_current_patient
    ),
) -> dict:

    booking = (
        await PatientBookingService.get_patient_booking(
            db=db,
            patient_id=current_patient.id,
            booking_id=booking_id,
        )
    )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking retrieved successfully",
        "data": data,
    }


# =========================================================
# PATIENT - RESCHEDULE OWN BOOKING
# =========================================================

@router.patch(
    "/my/{booking_id}/reschedule",
)
async def reschedule_my_booking(
    payload: PatientBookingRescheduleRequest,
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(
        get_current_patient
    ),
) -> dict:

    booking = (
        await PatientBookingService.get_patient_booking(
            db=db,
            patient_id=current_patient.id,
            booking_id=booking_id,
        )
    )

    booking = (
        await PatientBookingService.reschedule_booking(
            db=db,
            booking=booking,
            payload=payload,
        )
    )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking rescheduled successfully",
        "data": data,
    }


# =========================================================
# PATIENT - CANCEL OWN BOOKING
# =========================================================

@router.delete(
    "/my/{booking_id}",
)
async def cancel_my_booking(
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_patient: Patient = Depends(
        get_current_patient
    ),
) -> dict:

    booking = (
        await PatientBookingService.get_patient_booking(
            db=db,
            patient_id=current_patient.id,
            booking_id=booking_id,
        )
    )

    booking = (
        await PatientBookingService.cancel_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking cancelled successfully",
        "data": {
            "id": booking.id,
            "status": booking.status,
        },
    }


# =========================================================
# STAFF - CREATE BOOKING
# =========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_patient_booking(
    payload: StaffPatientBookingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "patient_booking.create"
        )
    ),
) -> dict:

    booking_payload = (
        PatientBookingCreateRequest(
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            reason=payload.reason,
        )
    )

    booking = (
        await PatientBookingService.create_booking(
            db=db,
            patient_id=payload.patient_id,
            payload=booking_payload,
        )
    )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Patient booking created successfully",
        "data": data,
    }


# =========================================================
# STAFF - LIST ALL
# =========================================================

@router.get(
    "",
)
async def list_patient_bookings(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "patient_booking.list"
        )
    ),
) -> dict:

    bookings = (
        await PatientBookingRepository.list_all(
            db=db,
            skip=skip,
            limit=limit,
        )
    )

    data = []

    for booking in bookings:
        data.append(
            await PatientBookingService.serialize_booking(
                db=db,
                booking=booking,
            )
        )

    return {
        "success": True,
        "message": "Patient bookings retrieved successfully",
        "data": data,
    }


# =========================================================
# STAFF - GET BOOKING
# =========================================================

@router.get(
    "/{booking_id}",
)
async def get_patient_booking(
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "patient_booking.view"
        )
    ),
) -> dict:

    booking = (
        await PatientBookingRepository.get_booking(
            db=db,
            booking_id=booking_id,
        )
    )

    if booking is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking retrieved successfully",
        "data": data,
    }


# =========================================================
# STAFF - RESCHEDULE
# =========================================================

@router.patch(
    "/{booking_id}/reschedule",
)
async def staff_reschedule_booking(
    payload: PatientBookingRescheduleRequest,
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "patient_booking.reschedule"
        )
    ),
) -> dict:

    booking = (
        await PatientBookingRepository.get_booking(
            db=db,
            booking_id=booking_id,
        )
    )

    if booking is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    booking = (
        await PatientBookingService.reschedule_booking(
            db=db,
            booking=booking,
            payload=payload,
        )
    )

    data = (
        await PatientBookingService.serialize_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking rescheduled successfully",
        "data": data,
    }


# =========================================================
# STAFF - CANCEL
# =========================================================

@router.delete(
    "/{booking_id}",
)
async def staff_cancel_booking(
    booking_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "patient_booking.cancel"
        )
    ),
) -> dict:

    booking = (
        await PatientBookingRepository.get_booking(
            db=db,
            booking_id=booking_id,
        )
    )

    if booking is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    booking = (
        await PatientBookingService.cancel_booking(
            db=db,
            booking=booking,
        )
    )

    return {
        "success": True,
        "message": "Booking cancelled successfully",
        "data": {
            "id": booking.id,
            "status": booking.status,
        },
    }
