from datetime import date

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.appointments.model import (
    Appointment,
    AppointmentSlot,
    AppointmentStatusHistory,
    AppointmentWaitingList,
    DoctorAvailability,
)
from app.modules.rbac.association import UserRole
from app.modules.rbac.model import Role
from app.modules.users.model import User


class AppointmentRepository:
    @staticmethod
    async def get_patient_active_appointment(
        db: AsyncSession,
        patient_id: int,
        appointment_date: date,
    ) -> Appointment | None:

        active_statuses = (
            "PENDING",
            "CONFIRMED",
            "CHECKED_IN",
            "IN_CONSULTATION",
        )

        result = await db.execute(
            select(Appointment)
            .where(
                Appointment.patient_id
                == patient_id,

                Appointment.appointment_date
                == appointment_date,

                Appointment.status.in_(
                    active_statuses
                ),
            )
            .order_by(
                Appointment.id.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    # =====================================================
    # DOCTOR AVAILABILITY
    # =====================================================

    @staticmethod
    async def create_availability(
        db: AsyncSession,
        availability: DoctorAvailability,
    ) -> DoctorAvailability:

        db.add(
            availability,
        )

        await db.flush()

        return availability

    @staticmethod
    async def get_availability_by_id(
        db: AsyncSession,
        availability_id: int,
    ) -> DoctorAvailability | None:

        result = await db.execute(
            select(
                DoctorAvailability,
            ).where(
                DoctorAvailability.id
                == availability_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_doctor_availability(
        db: AsyncSession,
        doctor_id: int,
    ) -> list[DoctorAvailability]:

        result = await db.execute(
            select(
                DoctorAvailability,
            )
            .where(
                DoctorAvailability.doctor_id
                == doctor_id,
            )
            .order_by(
                DoctorAvailability.day_of_week,
                DoctorAvailability.start_time,
            )
        )

        return list(
            result.scalars().all(),
        )

    @staticmethod
    async def get_active_availability_for_day(
        db: AsyncSession,
        doctor_id: int,
        day_of_week: int,
    ) -> list[DoctorAvailability]:

        result = await db.execute(
            select(
                DoctorAvailability,
            )
            .where(
                DoctorAvailability.doctor_id
                == doctor_id,
                DoctorAvailability.day_of_week
                == day_of_week,
                DoctorAvailability.is_active
                .is_(True),
            )
            .order_by(
                DoctorAvailability.start_time,
            )
        )

        return list(
            result.scalars().all(),
        )

    # =====================================================
    # SLOTS
    # =====================================================

    @staticmethod
    async def get_slot(
        db: AsyncSession,
        slot_id: int,
    ) -> AppointmentSlot | None:

        result = await db.execute(
            select(
                AppointmentSlot,
            ).where(
                AppointmentSlot.id
                == slot_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_slot_for_update(
        db: AsyncSession,
        slot_id: int,
    ) -> AppointmentSlot | None:

        result = await db.execute(
            select(
                AppointmentSlot,
            )
            .where(
                AppointmentSlot.id
                == slot_id,
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_slots_for_date(
        db: AsyncSession,
        doctor_id: int,
        slot_date: date,
    ) -> list[AppointmentSlot]:

        result = await db.execute(
            select(
                AppointmentSlot,
            )
            .where(
                AppointmentSlot.doctor_id
                == doctor_id,
                AppointmentSlot.slot_date
                == slot_date,
            )
            .order_by(
                AppointmentSlot.start_time,
            )
        )

        return list(
            result.scalars().all(),
        )

    @staticmethod
    async def get_future_unbooked_slots(
        db: AsyncSession,
        doctor_id: int,
        from_date: date,
    ) -> list[AppointmentSlot]:
        result = await db.execute(
            select(AppointmentSlot).where(
                AppointmentSlot.doctor_id == doctor_id,
                AppointmentSlot.slot_date >= from_date,
                AppointmentSlot.appointment_id.is_(None),
                AppointmentSlot.is_blocked.is_(False),
            )
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        doctor_id: int,
        appointment_date: date,
    ) -> list[AppointmentSlot]:

        result = await db.execute(
            select(AppointmentSlot)
            .where(
                AppointmentSlot.doctor_id
                == doctor_id,

                AppointmentSlot.slot_date
                == appointment_date,

                AppointmentSlot.is_available
                .is_(True),

                AppointmentSlot.is_blocked
                .is_(False),

                AppointmentSlot.appointment_id
                .is_(None),
            )
            .order_by(
                AppointmentSlot.start_time.asc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def find_existing_slot(
        db: AsyncSession,
        doctor_id: int,
        slot_date: date,
        start_time,
    ) -> AppointmentSlot | None:

        result = await db.execute(
            select(
                AppointmentSlot,
            ).where(
                AppointmentSlot.doctor_id
                == doctor_id,
                AppointmentSlot.slot_date
                == slot_date,
                AppointmentSlot.start_time
                == start_time,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create_slot(
        db: AsyncSession,
        slot: AppointmentSlot,
    ) -> AppointmentSlot:

        db.add(
            slot,
        )

        await db.flush()

        return slot

    # =====================================================
    # APPOINTMENTS
    # =====================================================

    @staticmethod
    async def create_appointment(
        db: AsyncSession,
        appointment: Appointment,
    ) -> Appointment:

        db.add(
            appointment,
        )

        await db.flush()

        return appointment

    @staticmethod
    async def get_appointment(
        db: AsyncSession,
        appointment_id: int,
    ) -> Appointment | None:

        result = await db.execute(
            select(
                Appointment,
            ).where(
                Appointment.id
                == appointment_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def list_appointments(
        db: AsyncSession,
        doctor_id: int | None = None,
        patient_id: int | None = None,
        appointment_date: date | None = None,
        status: str | None = None,
        appointment_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Appointment], int]:

        filters = []

        if doctor_id is not None:
            filters.append(
                Appointment.doctor_id
                == doctor_id,
            )

        if patient_id is not None:
            filters.append(
                Appointment.patient_id
                == patient_id,
            )

        if appointment_date is not None:
            filters.append(
                Appointment.appointment_date
                == appointment_date,
            )

        if status:
            filters.append(
                Appointment.status
                == status,
            )

        if appointment_type:
            filters.append(
                Appointment.appointment_type
                == appointment_type,
            )

        query = (
            select(
                Appointment,
            )
            .where(
                *filters,
            )
            .order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time.asc(),
            )
            .offset(
                (page - 1)
                * limit
            )
            .limit(
                limit,
            )
        )

        result = await db.execute(
            query,
        )

        appointments = list(
            result.scalars().all(),
        )

        count_query = (
            select(
                func.count(
                    Appointment.id,
                )
            )
            .where(
                *filters,
            )
        )

        total_result = (
            await db.execute(
                count_query,
            )
        )

        total = (
            total_result.scalar()
            or 0
        )

        return (
            appointments,
            total,
        )

    @staticmethod
    async def get_calendar_appointments(
        db: AsyncSession,
        start_date: date,
        end_date: date,
        doctor_id: int | None = None,
    ) -> list[Appointment]:

        filters = [
            Appointment.appointment_date
            >= start_date,
            Appointment.appointment_date
            <= end_date,
        ]

        if doctor_id is not None:
            filters.append(
                Appointment.doctor_id
                == doctor_id,
            )

        result = await db.execute(
            select(
                Appointment,
            )
            .where(
                *filters,
            )
            .order_by(
                Appointment.appointment_date,
                Appointment.start_time,
            )
        )

        return list(
            result.scalars().all(),
        )

    @staticmethod
    async def count_upcoming_patient_appointments(
        db: AsyncSession,
        patient_id: int,
        from_date: date,
    ) -> int:
        result = await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.patient_id == patient_id,
                Appointment.appointment_date >= from_date,
                Appointment.status.in_(
                    (
                        "PENDING",
                        "CONFIRMED",
                        "CHECKED_IN",
                        "IN_CONSULTATION",
                    )
                ),
            )
        )

        return result.scalar() or 0

    @staticmethod
    async def get_confirmed_appointments_until(
        db: AsyncSession,
        end_date: date,
    ) -> list[Appointment]:

        result = await db.execute(
            select(
                Appointment,
            )
            .where(
                Appointment.status
                == "CONFIRMED",
                Appointment.appointment_date
                <= end_date,
            )
        )

        return list(
            result.scalars().all(),
        )

    @staticmethod
    async def delete_appointment(
        db: AsyncSession,
        appointment: Appointment,
    ) -> None:

        await db.delete(
            appointment,
        )

        await db.flush()

    # =====================================================
    # STATUS HISTORY
    # =====================================================

    @staticmethod
    async def create_status_history(
        db: AsyncSession,
        history: AppointmentStatusHistory,
    ) -> AppointmentStatusHistory:

        db.add(
            history,
        )

        await db.flush()

        return history

    @staticmethod
    async def get_status_history(
        db: AsyncSession,
        appointment_id: int,
    ) -> list[AppointmentStatusHistory]:

        result = await db.execute(
            select(
                AppointmentStatusHistory,
            )
            .where(
                AppointmentStatusHistory.appointment_id
                == appointment_id,
            )
            .order_by(
                AppointmentStatusHistory.id,
            )
        )

        return list(
            result.scalars().all(),
        )

    # =====================================================
    # WAITING LIST
    # =====================================================

    @staticmethod
    async def create_waiting_list(
        db: AsyncSession,
        item: AppointmentWaitingList,
    ) -> AppointmentWaitingList:

        db.add(
            item,
        )

        await db.flush()

        return item

    @staticmethod
    async def get_waiting_list_item(
        db: AsyncSession,
        waiting_list_id: int,
    ) -> AppointmentWaitingList | None:

        result = await db.execute(
            select(
                AppointmentWaitingList,
            ).where(
                AppointmentWaitingList.id
                == waiting_list_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def list_waiting_list(
        db: AsyncSession,
        doctor_id: int | None = None,
    ) -> list[AppointmentWaitingList]:

        query = select(
            AppointmentWaitingList,
        )

        if doctor_id is not None:
            query = query.where(
                AppointmentWaitingList.doctor_id
                == doctor_id,
            )

        query = query.order_by(
            AppointmentWaitingList.priority.desc(),
            AppointmentWaitingList.preferred_date,
            AppointmentWaitingList.id,
        )

        result = await db.execute(
            query,
        )

        return list(
            result.scalars().all(),
        )

    @staticmethod
    async def get_duty_doctors(
        db: AsyncSession,
    ) -> list[User]:

        result = await db.execute(
            select(User)
            .join(
                UserRole,
                UserRole.user_id == User.id,
            )
            .join(
                Role,
                Role.id == UserRole.role_id,
            )
            .where(
                Role.name == "duty_doctor",
                Role.is_active.is_(True),
                User.is_active.is_(True),
            )
            .order_by(
                User.full_name.asc()
            )
        )

        return list(
            result
            .scalars()
            .unique()
            .all()
        )

    @staticmethod
    async def get_duty_doctor_by_id(
        db: AsyncSession,
        doctor_id: int,
    ) -> User | None:

        result = await db.execute(
            select(User)
            .join(
                UserRole,
                UserRole.user_id == User.id,
            )
            .join(
                Role,
                Role.id == UserRole.role_id,
            )
            .where(
                User.id == doctor_id,
                User.is_active.is_(True),

                Role.name == "duty_doctor",
                Role.is_active.is_(True),
            )
        )

        return result.scalars().unique().one_or_none()

    @staticmethod
    async def get_appointment_for_update(
        db: AsyncSession,
        appointment_id: int,
    ) -> Appointment | None:

        result = await db.execute(
            select(Appointment)
            .where(
                Appointment.id
                == appointment_id
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def add_status_history(
        db: AsyncSession,
        *,
        appointment_id: int,
        old_status: str | None,
        new_status: str,
        changed_by: int | None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> AppointmentStatusHistory:

        history = AppointmentStatusHistory(
            appointment_id=appointment_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        db.add(history)

        await db.flush()

        return history
