from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import get_db
from app.modules.appointments.repository import (
    AppointmentRepository,
)
from app.modules.appointments.schema import (
    AppointmentActionRequest,
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentUpdateRequest,
    AvailableSlotsResponse,
    DoctorAvailabilityCreateRequest,
    DoctorAvailabilityUpdateRequest,
    DoctorBookingAvailabilityResponse,
    DutyDoctorOptionResponse,
    FollowUpAppointmentRequest,
    ReceptionPatientStatusResponse,
    SlotBlockRequest,
    WaitingListCreateRequest,
    WaitingListUpdateRequest,
)
from app.modules.appointments.service import (
    AppointmentService,
)
from app.modules.rbac.dependencies import (
    require_permission,
)
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User


appointments_router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)

doctor_availability_router = APIRouter(
    prefix="/doctor-availability",
    tags=["Doctor Availability"],
)


# =========================================================
# RECEPTIONIST APPOINTMENT FLOW
# IMPORTANT: keep above /{appointment_id}
# =========================================================


@appointments_router.get(
    "/reception/patients/{patient_id}/status",
    response_model=ReceptionPatientStatusResponse,
)
async def reception_patient_status(
    patient_id: int,
    appointment_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.view",
        )
    ),
):
    return await AppointmentService.get_reception_patient_status(
        db=db,
        patient_id=patient_id,
        appointment_date=appointment_date,
    )


@appointments_router.get(
    "/reception/duty-doctors",
    response_model=list[DutyDoctorOptionResponse],
)
async def reception_duty_doctors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.view",
        )
    ),
):
    return await AppointmentService.get_reception_duty_doctors(
        db=db,
    )


@appointments_router.get(
    "/reception/duty-doctors/{doctor_id}/availability",
    response_model=DoctorBookingAvailabilityResponse,
)
async def reception_doctor_availability(
    doctor_id: int,
    appointment_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.view",
        )
    ),
):
    return await AppointmentService.get_doctor_booking_availability(
        db=db,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
    )


# =========================================================
# SLOT APIs
# =========================================================


@appointments_router.get(
    "/available-slots",
    response_model=AvailableSlotsResponse,
)
async def get_available_slots(
    doctor_id: int,
    appointment_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointment_slots.view",
        )
    ),
):
    slots = await AppointmentService.get_available_slots(
        db=db,
        doctor_id=doctor_id,
        slot_date=appointment_date,
    )

    return {
        "success": True,
        "message": "Available slots fetched successfully",
        "data": [
            {
                "id": slot.id,
                "slot_id": slot.id,
                "doctor_id": slot.doctor_id,
                "slot_date": slot.slot_date,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "is_available": slot.is_available,
                "is_blocked": slot.is_blocked,
                "appointment_id": slot.appointment_id,
            }
            for slot in slots
        ],
    }


@appointments_router.post(
    "/slots/{slot_id}/block",
)
async def block_or_unblock_slot(
    slot_id: int,
    payload: SlotBlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointment_slots.manage",
        )
    ),
):
    slot = await AppointmentService.block_slot(
        db=db,
        slot_id=slot_id,
        is_blocked=payload.is_blocked,
    )

    return {
        "success": True,
        "message": "Slot updated successfully",
        "data": slot,
    }


# =========================================================
# CALENDAR
# =========================================================


@appointments_router.get(
    "/calendar",
)
async def appointment_calendar(
    start_date: date,
    end_date: date,
    doctor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.view",
        )
    ),
):
    appointments = await AppointmentRepository.get_calendar_appointments(
        db=db,
        start_date=start_date,
        end_date=end_date,
        doctor_id=doctor_id,
    )

    return {
        "success": True,
        "message": "Appointment calendar fetched",
        "data": appointments,
    }


# =========================================================
# WAITING LIST
# =========================================================


@appointments_router.post(
    "/waiting-list",
)
async def add_to_waiting_list(
    payload: WaitingListCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointment_waiting_list.manage",
        )
    ),
):
    item = await AppointmentService.create_waiting_list_item(
        db,
        payload,
    )

    return {
        "success": True,
        "message": "Patient added to waiting list",
        "data": item,
    }


@appointments_router.get(
    "/waiting-list",
)
async def get_waiting_list(
    doctor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointment_waiting_list.view",
        )
    ),
):
    items = await AppointmentRepository.list_waiting_list(
        db,
        doctor_id,
    )

    return {
        "success": True,
        "data": items,
    }


@appointments_router.patch(
    "/waiting-list/{waiting_list_id}",
)
async def update_waiting_list(
    waiting_list_id: int,
    payload: WaitingListUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointment_waiting_list.manage",
        )
    ),
):
    item = await AppointmentService.update_waiting_list(
        db,
        waiting_list_id,
        payload,
    )

    return {
        "success": True,
        "message": "Waiting list updated",
        "data": item,
    }


# =========================================================
# NO SHOW AUTOMATION TEST ENDPOINT
# =========================================================


@appointments_router.post(
    "/automation/no-show",
)
async def run_no_show_automation(
    grace_minutes: int = Query(
        default=30,
        ge=0,
        le=240,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.no_show",
        )
    ),
):
    count = await AppointmentService.mark_expired_appointments_as_no_show(
        db=db,
        grace_minutes=grace_minutes,
    )

    return {
        "success": True,
        "message": f"{count} appointment(s) marked as NO_SHOW",
        "data": {
            "updated": count,
        },
    }


# =========================================================
# APPOINTMENT CRUD
# =========================================================


@appointments_router.post("")
async def create_appointment(
    payload: AppointmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.create",
        )
    ),
):
    appointment = await AppointmentService.create_appointment(
        db=db,
        payload=payload,
        created_by=current_user.id,
    )

    return {
        "success": True,
        "message": "Appointment created successfully",
        "data": appointment,
    }


@appointments_router.get("")
async def get_appointments(
    doctor_id: int | None = None,
    patient_id: int | None = None,
    appointment_date: date | None = None,
    appointment_status: str | None = Query(
        default=None,
        alias="status",
    ),
    appointment_type: str | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.view",
        )
    ),
):
    appointments, total = await AppointmentRepository.list_appointments(
        db=db,
        doctor_id=doctor_id,
        patient_id=patient_id,
        appointment_date=appointment_date,
        status=appointment_status,
        appointment_type=appointment_type,
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


# =========================================================
# STATUS ACTIONS
# Keep above generic /{appointment_id}
# =========================================================


@appointments_router.patch(
    "/{appointment_id}/confirm",
)
async def confirm_appointment(
    appointment_id: int,
    payload: AppointmentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.confirm",
        )
    ),
):
    appointment = await AppointmentService.confirm_appointment(
        db,
        appointment_id,
        current_user.id,
        payload,
    )

    return {
        "success": True,
        "message": "Appointment confirmed",
        "data": appointment,
    }


@appointments_router.patch(
    "/{appointment_id}/check-in",
)
async def check_in(
    appointment_id: int,
    payload: AppointmentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.checkin",
        )
    ),
):
    appointment = await AppointmentService.check_in(
        db,
        appointment_id,
        current_user.id,
        payload,
    )

    return {
        "success": True,
        "message": "Patient checked in",
        "data": appointment,
    }


@appointments_router.patch(
    "/{appointment_id}/start-consultation",
)
async def start_consultation(
    appointment_id: int,
    payload: AppointmentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.consult",
        )
    ),
):
    appointment = await AppointmentService.start_consultation(
        db,
        appointment_id,
        current_user.id,
        payload,
    )

    return {
        "success": True,
        "message": "Consultation started",
        "data": appointment,
    }


@appointments_router.patch(
    "/{appointment_id}/complete",
)
async def complete_appointment(
    appointment_id: int,
    payload: AppointmentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.complete",
        )
    ),
):
    appointment = await AppointmentService.complete_appointment(
        db,
        appointment_id,
        current_user.id,
        payload,
    )

    return {
        "success": True,
        "message": "Appointment completed",
        "data": appointment,
    }


@appointments_router.patch(
    "/{appointment_id}/no-show",
)
async def mark_no_show(
    appointment_id: int,
    payload: AppointmentActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.no_show",
        )
    ),
):
    appointment = await AppointmentService.mark_no_show(
        db,
        appointment_id,
        current_user.id,
        payload,
    )

    return {
        "success": True,
        "message": "Appointment marked as NO_SHOW",
        "data": appointment,
    }


# =========================================================
# RESCHEDULE
# =========================================================


@appointments_router.post(
    "/{appointment_id}/reschedule",
)
async def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.reschedule",
        )
    ),
):
    appointment = await AppointmentService.reschedule(
        db,
        appointment_id,
        payload,
        current_user.id,
    )

    return {
        "success": True,
        "message": "Appointment rescheduled successfully",
        "data": appointment,
    }


# =========================================================
# FOLLOW UP
# =========================================================


@appointments_router.post(
    "/{appointment_id}/follow-up",
)
async def create_follow_up(
    appointment_id: int,
    payload: FollowUpAppointmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.create",
        )
    ),
):
    appointment = await AppointmentService.create_follow_up(
        db,
        appointment_id,
        payload,
        current_user.id,
    )

    return {
        "success": True,
        "message": "Follow-up appointment created",
        "data": appointment,
    }


# =========================================================
# STATUS HISTORY
# =========================================================


@appointments_router.get(
    "/{appointment_id}/status-history",
)
async def get_status_history(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.view",
        )
    ),
):
    history = await AppointmentRepository.get_status_history(
        db,
        appointment_id,
    )

    return {
        "success": True,
        "data": history,
    }


# =========================================================
# GENERIC APPOINTMENT BY ID
# Keep after all static/action routes.
# =========================================================


@appointments_router.get(
    "/{appointment_id}",
)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.view",
        )
    ),
):
    appointment = await AppointmentRepository.get_appointment(
        db,
        appointment_id,
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    return {
        "success": True,
        "data": appointment,
    }


@appointments_router.put(
    "/{appointment_id}",
)
async def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.update",
        )
    ),
):
    appointment = await AppointmentService.update_appointment(
        db,
        appointment_id,
        payload,
    )

    return {
        "success": True,
        "message": "Appointment updated successfully",
        "data": appointment,
    }


@appointments_router.delete(
    "/{appointment_id}",
)
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "appointments.update",
        )
    ),
):
    await AppointmentService.delete_pending_appointment(
        db,
        appointment_id,
    )

    return {
        "success": True,
        "message": "Pending appointment deleted",
    }


# =========================================================
# DOCTOR AVAILABILITY ROUTES
# =========================================================


@doctor_availability_router.post("")
async def create_doctor_availability(
    payload: DoctorAvailabilityCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.manage",
            "doctor_availability.manage_own",
            require_all=False,
        )
    ),
):
    can_manage_all = await RBACRepository.user_has_permission(
        db=db,
        user_id=current_user.id,
        permission_code="doctor_availability.manage",
    )

    availability = await AppointmentService.create_doctor_availability(
        db=db,
        payload=payload,
        actor_id=current_user.id,
        can_manage_all=can_manage_all,
    )

    return {
        "success": True,
        "message": "Doctor availability created",
        "data": availability,
    }


@doctor_availability_router.get(
    "/{doctor_id}",
)
async def get_doctor_availability(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.view",
        )
    ),
):
    availability = await AppointmentRepository.get_doctor_availability(
        db,
        doctor_id,
    )

    return {
        "success": True,
        "data": availability,
    }


@doctor_availability_router.put(
    "/{availability_id}",
)
async def update_doctor_availability(
    availability_id: int,
    payload: DoctorAvailabilityUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.manage",
            "doctor_availability.manage_own",
            require_all=False,
        )
    ),
):
    can_manage_all = await RBACRepository.user_has_permission(
        db=db,
        user_id=current_user.id,
        permission_code="doctor_availability.manage",
    )

    availability = await AppointmentService.update_doctor_availability(
        db=db,
        availability_id=availability_id,
        payload=payload,
        actor_id=current_user.id,
        can_manage_all=can_manage_all,
    )

    return {
        "success": True,
        "message": "Doctor availability updated",
        "data": availability,
    }


@doctor_availability_router.delete(
    "/{availability_id}",
)
async def delete_doctor_availability(
    availability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "doctor_availability.manage",
            "doctor_availability.manage_own",
            require_all=False,
        )
    ),
):
    can_manage_all = await RBACRepository.user_has_permission(
        db=db,
        user_id=current_user.id,
        permission_code="doctor_availability.manage",
    )

    await AppointmentService.delete_doctor_availability(
        db=db,
        availability_id=availability_id,
        actor_id=current_user.id,
        can_manage_all=can_manage_all,
    )

    return {
        "success": True,
        "message": "Doctor availability disabled",
    }
