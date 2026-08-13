from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schema import (
    PatientAppointmentCreateRequest,
)
from app.modules.appointments.service import AppointmentService
from app.modules.patients.constants import PatientStatus
from app.modules.patients.portal.dependencies import (
    CurrentPatient,
    CurrentPatientUser,
)


router = APIRouter(prefix="/appointments")


def ensure_patient_can_book(current_patient: CurrentPatient) -> None:
    if current_patient.status != PatientStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active patients can book appointments",
        )


@router.get("/available-slots")
async def get_patient_available_slots(
    current_patient: CurrentPatient,
    doctor_id: int = Query(gt=0),
    appointment_date: date = Query(),
    db: AsyncSession = Depends(get_db),
):
    ensure_patient_can_book(current_patient)

    slots = await AppointmentService.get_available_slots(
        db=db,
        doctor_id=doctor_id,
        slot_date=appointment_date,
    )

    return {
        "success": True,
        "message": "Available slots fetched successfully",
        "data": slots,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_patient_appointment(
    payload: PatientAppointmentCreateRequest,
    current_patient: CurrentPatient,
    current_user: CurrentPatientUser,
    db: AsyncSession = Depends(get_db),
):
    ensure_patient_can_book(current_patient)

    appointment = await AppointmentService.create_patient_appointment(
        db=db,
        payload=payload,
        patient_id=current_patient.id,
        created_by=current_user.id,
    )

    return {
        "success": True,
        "message": "Online appointment booked successfully",
        "data": appointment,
    }


@router.get("")
async def list_patient_appointments(
    current_patient: CurrentPatient,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    appointments, total = await AppointmentRepository.list_appointments(
        db=db,
        patient_id=current_patient.id,
        page=page,
        limit=limit,
    )

    return {
        "success": True,
        "message": "Appointments fetched successfully",
        "data": appointments,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
        },
    }


@router.get("/{appointment_id}")
async def get_patient_appointment(
    appointment_id: int,
    current_patient: CurrentPatient,
    db: AsyncSession = Depends(get_db),
):
    appointment = await AppointmentRepository.get_appointment(
        db=db,
        appointment_id=appointment_id,
    )

    if appointment is None or appointment.patient_id != current_patient.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    return {
        "success": True,
        "data": appointment,
    }
