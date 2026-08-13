from datetime import date, datetime, timedelta

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.appointments.enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.modules.appointments.model import (
    Appointment,
    AppointmentSlot,
    AppointmentStatusHistory,
    AppointmentWaitingList,
    DoctorAvailability,
)
from app.modules.appointments.repository import (
    AppointmentRepository,
)
from app.modules.appointments.schema import (
    AppointmentActionRequest,
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentUpdateRequest,
    DoctorAvailabilityCreateRequest,
    DoctorAvailabilityUpdateRequest,
    FollowUpAppointmentRequest,
    WaitingListCreateRequest,
    WaitingListUpdateRequest,
)
from app.modules.appointments.utils import (
    generate_appointment_number,
    generate_time_slots,
    now_local,
    today_local,
)


VALID_STATUS_TRANSITIONS = {
    AppointmentStatus.PENDING.value: {
        AppointmentStatus.CONFIRMED.value,
        AppointmentStatus.RESCHEDULED.value,
    },

    AppointmentStatus.CONFIRMED.value: {
        AppointmentStatus.CHECKED_IN.value,
        AppointmentStatus.RESCHEDULED.value,
        AppointmentStatus.NO_SHOW.value,
    },

    AppointmentStatus.CHECKED_IN.value: {
        AppointmentStatus.IN_CONSULTATION.value,
    },

    AppointmentStatus.IN_CONSULTATION.value: {
        AppointmentStatus.COMPLETED.value,
    },

    AppointmentStatus.COMPLETED.value: set(),

    AppointmentStatus.RESCHEDULED.value: set(),

    AppointmentStatus.NO_SHOW.value: set(),
}


class AppointmentService:

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    @staticmethod
    def _validate_time_range(
        start_time,
        end_time,
    ) -> None:

        if start_time >= end_time:
            raise HTTPException(
        status_code=422,
        detail=(
            "start_time must be earlier "
            "than end_time"
        ),
    )

    @staticmethod
    async def _create_history(
        db: AsyncSession,
        appointment_id: int,
        old_status: str | None,
        new_status: str,
        changed_by: int | None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> None:

        history = AppointmentStatusHistory(
            appointment_id=appointment_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        await AppointmentRepository.create_status_history(
            db,
            history,
        )

    @staticmethod
    async def _change_status(
        db: AsyncSession,
        appointment: Appointment,
        new_status: str,
        changed_by: int | None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> Appointment:

        old_status = (
            appointment.status
        )

        allowed_statuses = (
            VALID_STATUS_TRANSITIONS.get(
                old_status,
                set(),
            )
        )

        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Invalid appointment "
                    f"status transition: "
                    f"{old_status} -> "
                    f"{new_status}"
                ),
            )

        appointment.status = (
            new_status
        )

        await AppointmentService._create_history(
            db=db,
            appointment_id=appointment.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        return appointment

    # =====================================================
    # DOCTOR AVAILABILITY
    # =====================================================

    @staticmethod
    async def create_doctor_availability(
        db: AsyncSession,
        payload: DoctorAvailabilityCreateRequest,
    ) -> DoctorAvailability:

        AppointmentService._validate_time_range(
            payload.start_time,
            payload.end_time,
        )

        availability = DoctorAvailability(
            doctor_id=payload.doctor_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            slot_duration_minutes=(
                payload.slot_duration_minutes
            ),
            is_active=payload.is_active,
        )

        try:
            await AppointmentRepository.create_availability(
                db,
                availability,
            )

            await db.commit()

            await db.refresh(
                availability,
            )

            return availability

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def update_doctor_availability(
        db: AsyncSession,
        availability_id: int,
        payload: DoctorAvailabilityUpdateRequest,
    ) -> DoctorAvailability:

        availability = (
            await AppointmentRepository.get_availability_by_id(
                db,
                availability_id,
            )
        )

        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Doctor availability "
                    "not found"
                ),
            )

        update_data = (
            payload.model_dump(
                exclude_unset=True,
            )
        )

        for field, value in (
            update_data.items()
        ):
            setattr(
                availability,
                field,
                value,
            )

        AppointmentService._validate_time_range(
            availability.start_time,
            availability.end_time,
        )

        try:
            await db.commit()

            await db.refresh(
                availability,
            )

            return availability

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_doctor_availability(
        db: AsyncSession,
        availability_id: int,
    ) -> None:

        availability = (
            await AppointmentRepository.get_availability_by_id(
                db,
                availability_id,
            )
        )

        if not availability:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Doctor availability "
                    "not found"
                ),
            )

        availability.is_active = False

        try:
            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # SLOT GENERATION
    # =====================================================

    @staticmethod
    async def ensure_slots_for_date(
        db: AsyncSession,
        doctor_id: int,
        slot_date: date,
    ) -> list[AppointmentSlot]:

        if slot_date < today_local():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Cannot generate slots "
                    "for a past date"
                ),
            )

        day_of_week = (
            slot_date.weekday()
        )

        availabilities = (
            await AppointmentRepository.get_active_availability_for_day(
                db,
                doctor_id,
                day_of_week,
            )
        )

        if not availabilities:
            return []

        created_any = False

        try:
            for availability in availabilities:

                time_slots = (
                    generate_time_slots(
                        slot_date=slot_date,
                        start_time=(
                            availability.start_time
                        ),
                        end_time=(
                            availability.end_time
                        ),
                        duration_minutes=(
                            availability.slot_duration_minutes
                        ),
                    )
                )

                for (
                    slot_start,
                    slot_end,
                ) in time_slots:

                    existing = (
                        await AppointmentRepository.find_existing_slot(
                            db=db,
                            doctor_id=doctor_id,
                            slot_date=slot_date,
                            start_time=slot_start,
                        )
                    )

                    if existing:
                        continue

                    slot = AppointmentSlot(
                        doctor_id=doctor_id,
                        slot_date=slot_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        is_available=True,
                        is_blocked=False,
                    )

                    await AppointmentRepository.create_slot(
                        db,
                        slot,
                    )

                    created_any = True

            if created_any:
                await db.commit()

            return (
                await AppointmentRepository.get_slots_for_date(
                    db,
                    doctor_id,
                    slot_date,
                )
            )

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        doctor_id: int,
        slot_date: date,
    ) -> list[AppointmentSlot]:

        await AppointmentService.ensure_slots_for_date(
            db=db,
            doctor_id=doctor_id,
            slot_date=slot_date,
        )

        return (
            await AppointmentRepository.get_available_slots(
                db,
                doctor_id,
                slot_date,
            )
        )

    @staticmethod
    async def block_slot(
        db: AsyncSession,
        slot_id: int,
        is_blocked: bool,
    ) -> AppointmentSlot:

        slot = (
            await AppointmentRepository.get_slot_for_update(
                db,
                slot_id,
            )
        )

        if not slot:
            raise HTTPException(
                status_code=404,
                detail="Slot not found",
            )

        if (
            slot.appointment_id is not None
            and is_blocked
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cannot block a slot "
                    "that already has an "
                    "appointment"
                ),
            )

        slot.is_blocked = (
            is_blocked
        )

        slot.is_available = (
            not is_blocked
            and slot.appointment_id
            is None
        )

        try:
            await db.commit()

            await db.refresh(
                slot,
            )

            return slot

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # CREATE APPOINTMENT
    # =====================================================

    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        payload: AppointmentCreateRequest,
        created_by: int | None,
    ) -> Appointment:

        try:
            # FOR UPDATE prevents double booking.
            slot = (
                await AppointmentRepository.get_slot_for_update(
                    db,
                    payload.slot_id,
                )
            )

            if not slot:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment slot not found",
                )

            if slot.doctor_id != payload.doctor_id:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Selected slot does not "
                        "belong to this doctor"
                    ),
                )

            if slot.slot_date < today_local():
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Cannot book an "
                        "appointment in the past"
                    ),
                )

            if slot.is_blocked:
                raise HTTPException(
                    status_code=409,
                    detail="Selected slot is blocked",
                )

            if (
                not slot.is_available
                or slot.appointment_id
                is not None
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Selected appointment "
                        "slot is no longer available"
                    ),
                )

            appointment = Appointment(
                appointment_number=(
                    generate_appointment_number()
                ),
                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                slot_id=slot.id,
                appointment_type=(
                    payload.appointment_type.value
                ),
                appointment_date=(
                    slot.slot_date
                ),
                start_time=(
                    slot.start_time
                ),
                end_time=(
                    slot.end_time
                ),
                reason=payload.reason,
                notes=payload.notes,
                status=(
                    AppointmentStatus.PENDING.value
                ),
                booking_source=(
                    payload.booking_source.value
                ),
                created_by=created_by,
            )

            await AppointmentRepository.create_appointment(
                db,
                appointment,
            )

            slot.is_available = False
            slot.appointment_id = (
                appointment.id
            )

            await AppointmentService._create_history(
                db=db,
                appointment_id=(
                    appointment.id
                ),
                old_status=None,
                new_status=(
                    AppointmentStatus.PENDING.value
                ),
                changed_by=created_by,
                reason="Appointment created",
            )

            await db.commit()

            await db.refresh(
                appointment,
            )

            return appointment

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # UPDATE BASIC DETAILS
    # =====================================================

    @staticmethod
    async def update_appointment(
        db: AsyncSession,
        appointment_id: int,
        payload: AppointmentUpdateRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        if appointment.status in {
            AppointmentStatus.COMPLETED.value,
            AppointmentStatus.NO_SHOW.value,
            AppointmentStatus.RESCHEDULED.value,
        }:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This appointment can "
                    "no longer be edited"
                ),
            )

        data = payload.model_dump(
            exclude_unset=True,
        )

        for field, value in data.items():
            setattr(
                appointment,
                field,
                value,
            )

        try:
            await db.commit()

            await db.refresh(
                appointment,
            )

            return appointment

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # CONFIRM
    # =====================================================

    @staticmethod
    async def confirm_appointment(
        db: AsyncSession,
        appointment_id: int,
        changed_by: int | None,
        payload: AppointmentActionRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        await AppointmentService._change_status(
            db=db,
            appointment=appointment,
            new_status=(
                AppointmentStatus.CONFIRMED.value
            ),
            changed_by=changed_by,
            reason=payload.reason,
            notes=payload.notes,
        )

        await db.commit()

        await db.refresh(
            appointment,
        )

        return appointment

    # =====================================================
    # CHECK IN
    # =====================================================

    @staticmethod
    async def check_in(
        db: AsyncSession,
        appointment_id: int,
        changed_by: int | None,
        payload: AppointmentActionRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        await AppointmentService._change_status(
            db=db,
            appointment=appointment,
            new_status=(
                AppointmentStatus.CHECKED_IN.value
            ),
            changed_by=changed_by,
            reason=payload.reason,
            notes=payload.notes,
        )

        appointment.checked_in_at = (
            now_local()
        )

        await db.commit()

        await db.refresh(
            appointment,
        )

        return appointment

    # =====================================================
    # START CONSULTATION
    # =====================================================

    @staticmethod
    async def start_consultation(
        db: AsyncSession,
        appointment_id: int,
        changed_by: int | None,
        payload: AppointmentActionRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        await AppointmentService._change_status(
            db=db,
            appointment=appointment,
            new_status=(
                AppointmentStatus.IN_CONSULTATION.value
            ),
            changed_by=changed_by,
            reason=payload.reason,
            notes=payload.notes,
        )

        appointment.consultation_started_at = (
            now_local()
        )

        await db.commit()

        await db.refresh(
            appointment,
        )

        return appointment

    # =====================================================
    # COMPLETE
    # =====================================================

    @staticmethod
    async def complete_appointment(
        db: AsyncSession,
        appointment_id: int,
        changed_by: int | None,
        payload: AppointmentActionRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        await AppointmentService._change_status(
            db=db,
            appointment=appointment,
            new_status=(
                AppointmentStatus.COMPLETED.value
            ),
            changed_by=changed_by,
            reason=payload.reason,
            notes=payload.notes,
        )

        appointment.completed_at = (
            now_local()
        )

        await db.commit()

        await db.refresh(
            appointment,
        )

        return appointment

    # =====================================================
    # NO SHOW
    # =====================================================

    @staticmethod
    async def mark_no_show(
        db: AsyncSession,
        appointment_id: int,
        changed_by: int | None,
        payload: AppointmentActionRequest,
    ) -> Appointment:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        await AppointmentService._change_status(
            db=db,
            appointment=appointment,
            new_status=(
                AppointmentStatus.NO_SHOW.value
            ),
            changed_by=changed_by,
            reason=payload.reason,
            notes=payload.notes,
        )

        appointment.no_show_at = (
            now_local()
        )

        await db.commit()

        await db.refresh(
            appointment,
        )

        return appointment

    # =====================================================
    # RESCHEDULE
    # =====================================================

    @staticmethod
    async def reschedule(
        db: AsyncSession,
        appointment_id: int,
        payload: AppointmentRescheduleRequest,
        changed_by: int | None,
    ) -> Appointment:

        old_appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not old_appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        if old_appointment.status not in {
            AppointmentStatus.PENDING.value,
            AppointmentStatus.CONFIRMED.value,
        }:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Only PENDING or CONFIRMED "
                    "appointments can be "
                    "rescheduled"
                ),
            )

        try:
            new_slot = (
                await AppointmentRepository.get_slot_for_update(
                    db,
                    payload.slot_id,
                )
            )

            if not new_slot:
                raise HTTPException(
                    status_code=404,
                    detail="New slot not found",
                )

            if (
                not new_slot.is_available
                or new_slot.is_blocked
                or new_slot.appointment_id
                is not None
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Selected new slot "
                        "is unavailable"
                    ),
                )

            if (
                new_slot.slot_date
                < today_local()
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Cannot reschedule "
                        "to a past date"
                    ),
                )

            old_status = (
                old_appointment.status
            )

            await AppointmentService._change_status(
                db=db,
                appointment=old_appointment,
                new_status=(
                    AppointmentStatus.RESCHEDULED.value
                ),
                changed_by=changed_by,
                reason=payload.reason,
            )

            # Release old slot.
            if old_appointment.slot_id:

                old_slot = (
                    await AppointmentRepository.get_slot_for_update(
                        db,
                        old_appointment.slot_id,
                    )
                )

                if old_slot:
                    old_slot.appointment_id = None

                    if not old_slot.is_blocked:
                        old_slot.is_available = True

            # Preserve confirmation state.
            if (
                old_status
                == AppointmentStatus.CONFIRMED.value
            ):
                new_status = (
                    AppointmentStatus.CONFIRMED.value
                )
            else:
                new_status = (
                    AppointmentStatus.PENDING.value
                )

            new_appointment = Appointment(
                appointment_number=(
                    generate_appointment_number()
                ),
                patient_id=(
                    old_appointment.patient_id
                ),
                doctor_id=(
                    new_slot.doctor_id
                ),
                slot_id=new_slot.id,
                appointment_type=(
                    old_appointment.appointment_type
                ),
                appointment_date=(
                    new_slot.slot_date
                ),
                start_time=(
                    new_slot.start_time
                ),
                end_time=(
                    new_slot.end_time
                ),
                reason=(
                    old_appointment.reason
                ),
                notes=(
                    old_appointment.notes
                ),
                status=new_status,
                booking_source=(
                    old_appointment.booking_source
                ),
                created_by=changed_by,
                parent_appointment_id=(
                    old_appointment.parent_appointment_id
                ),
                rescheduled_from_id=(
                    old_appointment.id
                ),
            )

            await AppointmentRepository.create_appointment(
                db,
                new_appointment,
            )

            new_slot.is_available = False
            new_slot.appointment_id = (
                new_appointment.id
            )

            await AppointmentService._create_history(
                db=db,
                appointment_id=(
                    new_appointment.id
                ),
                old_status=None,
                new_status=new_status,
                changed_by=changed_by,
                reason=(
                    "Created from rescheduled "
                    f"appointment "
                    f"{old_appointment.appointment_number}"
                ),
            )

            await db.commit()

            await db.refresh(
                new_appointment,
            )

            return new_appointment

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # FOLLOW UP
    # =====================================================

    @staticmethod
    async def create_follow_up(
        db: AsyncSession,
        appointment_id: int,
        payload: FollowUpAppointmentRequest,
        created_by: int | None,
    ) -> Appointment:

        parent = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        if (
            parent.status
            != AppointmentStatus.COMPLETED.value
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Follow-up can only be "
                    "scheduled after the "
                    "appointment is completed"
                ),
            )

        try:
            slot = (
                await AppointmentRepository.get_slot_for_update(
                    db,
                    payload.slot_id,
                )
            )

            if not slot:
                raise HTTPException(
                    status_code=404,
                    detail="Follow-up slot not found",
                )

            if (
                not slot.is_available
                or slot.is_blocked
                or slot.appointment_id
                is not None
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Selected follow-up "
                        "slot is unavailable"
                    ),
                )

            if (
                slot.slot_date
                < today_local()
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Follow-up date cannot "
                        "be in the past"
                    ),
                )

            appointment = Appointment(
                appointment_number=(
                    generate_appointment_number()
                ),
                patient_id=(
                    parent.patient_id
                ),
                doctor_id=(
                    slot.doctor_id
                ),
                slot_id=slot.id,
                appointment_type=(
                    AppointmentType.FOLLOW_UP.value
                ),
                appointment_date=(
                    slot.slot_date
                ),
                start_time=(
                    slot.start_time
                ),
                end_time=(
                    slot.end_time
                ),
                reason=payload.reason,
                notes=payload.notes,
                status=(
                    AppointmentStatus.PENDING.value
                ),
                booking_source=(
                    parent.booking_source
                ),
                created_by=created_by,
                parent_appointment_id=(
                    parent.id
                ),
            )

            await AppointmentRepository.create_appointment(
                db,
                appointment,
            )

            slot.is_available = False
            slot.appointment_id = (
                appointment.id
            )

            await AppointmentService._create_history(
                db=db,
                appointment_id=(
                    appointment.id
                ),
                old_status=None,
                new_status=(
                    AppointmentStatus.PENDING.value
                ),
                changed_by=created_by,
                reason=(
                    "Follow-up appointment created"
                ),
            )

            await db.commit()

            await db.refresh(
                appointment,
            )

            return appointment

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # DELETE PENDING APPOINTMENT
    # =====================================================

    @staticmethod
    async def delete_pending_appointment(
        db: AsyncSession,
        appointment_id: int,
    ) -> None:

        appointment = (
            await AppointmentRepository.get_appointment(
                db,
                appointment_id,
            )
        )

        if not appointment:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found",
            )

        # Clinical appointment records should
        # not normally be hard deleted.
        if (
            appointment.status
            != AppointmentStatus.PENDING.value
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Only PENDING appointments "
                    "can be deleted"
                ),
            )

        try:
            if appointment.slot_id:

                slot = (
                    await AppointmentRepository.get_slot_for_update(
                        db,
                        appointment.slot_id,
                    )
                )

                if slot:
                    slot.appointment_id = None

                    if not slot.is_blocked:
                        slot.is_available = True

            await AppointmentRepository.delete_appointment(
                db,
                appointment,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # =====================================================
    # WAITING LIST
    # =====================================================

    @staticmethod
    async def create_waiting_list_item(
        db: AsyncSession,
        payload: WaitingListCreateRequest,
    ) -> AppointmentWaitingList:

        if (
            payload.preferred_date
            < today_local()
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Preferred date cannot "
                    "be in the past"
                ),
            )

        item = AppointmentWaitingList(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            preferred_date=(
                payload.preferred_date
            ),
            preferred_start_time=(
                payload.preferred_start_time
            ),
            preferred_end_time=(
                payload.preferred_end_time
            ),
            priority=payload.priority,
            status="WAITING",
            notes=payload.notes,
        )

        try:
            await AppointmentRepository.create_waiting_list(
                db,
                item,
            )

            await db.commit()

            await db.refresh(
                item,
            )

            return item

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def update_waiting_list(
        db: AsyncSession,
        waiting_list_id: int,
        payload: WaitingListUpdateRequest,
    ) -> AppointmentWaitingList:

        item = (
            await AppointmentRepository.get_waiting_list_item(
                db,
                waiting_list_id,
            )
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Waiting list record "
                    "not found"
                ),
            )

        item.status = (
            payload.status.value
        )

        if payload.notes is not None:
            item.notes = payload.notes

        await db.commit()

        await db.refresh(
            item,
        )

        return item

    # =====================================================
    # AUTOMATIC NO SHOW
    # =====================================================

    @staticmethod
    async def mark_expired_appointments_as_no_show(
        db: AsyncSession,
        grace_minutes: int = 30,
    ) -> int:

        current_time = (
            now_local()
        )

        candidates = (
            await AppointmentRepository.get_confirmed_appointments_until(
                db,
                current_time.date(),
            )
        )

        updated_count = 0

        try:
            for appointment in candidates:

                appointment_end = (
                    datetime.combine(
                        appointment.appointment_date,
                        appointment.end_time,
                    )
                )

                no_show_after = (
                    appointment_end
                    + timedelta(
                        minutes=grace_minutes,
                    )
                )

                if (
                    current_time
                    <= no_show_after
                ):
                    continue

                await AppointmentService._change_status(
                    db=db,
                    appointment=appointment,
                    new_status=(
                        AppointmentStatus.NO_SHOW.value
                    ),
                    changed_by=None,
                    reason=(
                        "Automatically marked "
                        "as no-show"
                    ),
                )

                appointment.no_show_at = (
                    current_time
                )

                updated_count += 1

            await db.commit()

            return updated_count

        except Exception:
            await db.rollback()
            raise