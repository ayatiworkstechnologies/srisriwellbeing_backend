from decimal import Decimal
from typing import Any

from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.orm import (
    selectinload,
)

from app.modules.treatment_plans.models import (
    TreatmentPlan,
    TreatmentPlanItem,
    TreatmentPlanMedicine,
    TreatmentPlanSpecialist,
    TreatmentPlanStatusHistory,
    TreatmentPlanTherapy,
    TreatmentPlanVersion,
)


class TreatmentPlanRepository:

    # ========================================================
    # TREATMENT PLAN - CREATE
    # ========================================================

    @staticmethod
    async def create_plan(
        db: AsyncSession,
        *,
        data: dict[str, Any],
        created_by: int,
    ) -> TreatmentPlan:

        plan = TreatmentPlan(
            **data,
            created_by=created_by,
            status="DRAFT",
            current_version=1,
        )

        db.add(plan)

        await db.flush()

        await db.refresh(
            plan
        )

        return plan

    # ========================================================
    # TREATMENT PLAN - GET
    # ========================================================

    @staticmethod
    async def get_plan(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> TreatmentPlan | None:

        statement = (
            select(
                TreatmentPlan
            )
            .where(
                TreatmentPlan.id
                == plan_id
            )
        )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # TREATMENT PLAN - FULL DETAILS
    # ========================================================

    @staticmethod
    async def get_plan_with_details(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> TreatmentPlan | None:

        statement = (
            select(
                TreatmentPlan
            )
            .options(
                selectinload(
                    TreatmentPlan.therapies
                ),
                selectinload(
                    TreatmentPlan.medicines
                ),
                selectinload(
                    TreatmentPlan.items
                ),
                selectinload(
                    TreatmentPlan.specialists
                ),
                selectinload(
                    TreatmentPlan.versions
                ),
                selectinload(
                    TreatmentPlan.status_history
                ),
            )
            .where(
                TreatmentPlan.id
                == plan_id
            )
        )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # LIST MY TREATMENT PLANS
    # ========================================================

    @staticmethod
    async def list_my_plans(
        db: AsyncSession,
        *,
        user_id: int,
        status: str | None = None,
        page: int = 1,
        limit: int = 100,
    ) -> list[TreatmentPlan]:

        statement = (
            select(
                TreatmentPlan
            )
            .where(
                TreatmentPlan.created_by
                == user_id
            )
        )

        if status:
            statement = (
                statement.where(
                    TreatmentPlan.status
                    == status
                )
            )

        statement = (
            statement
            .order_by(
                TreatmentPlan.id.desc()
            )
            .offset(
                (page - 1) * limit
            )
            .limit(
                limit
            )
        )

        result = await db.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # LIST PATIENT TREATMENT PLANS
    # ========================================================

    @staticmethod
    async def list_patient_plans(
        db: AsyncSession,
        *,
        patient_id: int,
    ) -> list[TreatmentPlan]:

        statement = (
            select(
                TreatmentPlan
            )
            .where(
                TreatmentPlan.patient_id
                == patient_id
            )
            .order_by(
                TreatmentPlan.id.desc()
            )
        )

        result = await db.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # FIND PLAN BY REFERRAL
    # ========================================================

    @staticmethod
    async def get_plan_by_referral(
        db: AsyncSession,
        *,
        referral_id: int,
    ) -> TreatmentPlan | None:

        statement = (
            select(
                TreatmentPlan
            )
            .where(
                TreatmentPlan.referral_id
                == referral_id
            )
            .order_by(
                TreatmentPlan.id.desc()
            )
        )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # UPDATE PLAN
    # ========================================================

    @staticmethod
    async def update_plan(
        db: AsyncSession,
        *,
        plan: TreatmentPlan,
        data: dict[str, Any],
    ) -> TreatmentPlan:

        for key, value in data.items():

            if hasattr(
                plan,
                key,
            ):
                setattr(
                    plan,
                    key,
                    value,
                )

        await db.flush()

        await db.refresh(
            plan
        )

        return plan

    # ========================================================
    # DELETE PLAN
    # ========================================================

    @staticmethod
    async def delete_plan(
        db: AsyncSession,
        *,
        plan: TreatmentPlan,
    ) -> None:

        await db.delete(
            plan
        )

        await db.flush()

    # ========================================================
    # THERAPY - CREATE
    # ========================================================

    @staticmethod
    async def create_therapy(
        db: AsyncSession,
        *,
        plan_id: int,
        data: dict[str, Any],
    ) -> TreatmentPlanTherapy:

        sessions = int(
            data.get(
                "sessions",
                1,
            )
        )

        unit_price = Decimal(
            str(
                data.get(
                    "unit_price",
                    0,
                )
            )
        )

        total_price = (
            Decimal(
                sessions
            )
            * unit_price
        )

        therapy = (
            TreatmentPlanTherapy(
                treatment_plan_id=plan_id,
                **data,
                total_price=total_price,
            )
        )

        db.add(
            therapy
        )

        await db.flush()

        await db.refresh(
            therapy
        )

        return therapy

    # ========================================================
    # THERAPY - GET
    # ========================================================

    @staticmethod
    async def get_therapy(
        db: AsyncSession,
        *,
        therapy_item_id: int,
        plan_id: int | None = None,
    ) -> TreatmentPlanTherapy | None:

        statement = (
            select(
                TreatmentPlanTherapy
            )
            .where(
                TreatmentPlanTherapy.id
                == therapy_item_id
            )
        )

        if plan_id:
            statement = (
                statement.where(
                    TreatmentPlanTherapy
                    .treatment_plan_id
                    == plan_id
                )
            )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # THERAPY - LIST
    # ========================================================

    @staticmethod
    async def list_therapies(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[TreatmentPlanTherapy]:

        result = await db.execute(
            select(
                TreatmentPlanTherapy
            )
            .where(
                TreatmentPlanTherapy
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanTherapy
                .id
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # THERAPY - UPDATE
    # ========================================================

    @staticmethod
    async def update_therapy(
        db: AsyncSession,
        *,
        therapy: TreatmentPlanTherapy,
        data: dict[str, Any],
    ) -> TreatmentPlanTherapy:

        for key, value in data.items():

            if hasattr(
                therapy,
                key,
            ):
                setattr(
                    therapy,
                    key,
                    value,
                )

        therapy.total_price = (
            Decimal(
                therapy.sessions
            )
            * Decimal(
                therapy.unit_price
            )
        )

        await db.flush()

        await db.refresh(
            therapy
        )

        return therapy

    # ========================================================
    # THERAPY - DELETE
    # ========================================================

    @staticmethod
    async def delete_therapy(
        db: AsyncSession,
        *,
        therapy: TreatmentPlanTherapy,
    ) -> None:

        await db.delete(
            therapy
        )

        await db.flush()

    # ========================================================
    # MEDICINE - CREATE
    # ========================================================

    @staticmethod
    async def create_medicine(
        db: AsyncSession,
        *,
        plan_id: int,
        data: dict[str, Any],
    ) -> TreatmentPlanMedicine:

        quantity = Decimal(
            str(
                data.get(
                    "quantity",
                    1,
                )
            )
        )

        unit_price = Decimal(
            str(
                data.get(
                    "unit_price",
                    0,
                )
            )
        )

        total_price = (
            quantity
            * unit_price
        )

        medicine = (
            TreatmentPlanMedicine(
                treatment_plan_id=plan_id,
                **data,
                total_price=total_price,
            )
        )

        db.add(
            medicine
        )

        await db.flush()

        await db.refresh(
            medicine
        )

        return medicine

    # ========================================================
    # MEDICINE - GET
    # ========================================================

    @staticmethod
    async def get_medicine(
        db: AsyncSession,
        *,
        medicine_item_id: int,
        plan_id: int | None = None,
    ) -> TreatmentPlanMedicine | None:

        statement = (
            select(
                TreatmentPlanMedicine
            )
            .where(
                TreatmentPlanMedicine.id
                == medicine_item_id
            )
        )

        if plan_id:
            statement = (
                statement.where(
                    TreatmentPlanMedicine
                    .treatment_plan_id
                    == plan_id
                )
            )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # MEDICINE - LIST
    # ========================================================

    @staticmethod
    async def list_medicines(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[TreatmentPlanMedicine]:

        result = await db.execute(
            select(
                TreatmentPlanMedicine
            )
            .where(
                TreatmentPlanMedicine
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanMedicine
                .id
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # MEDICINE - UPDATE
    # ========================================================

    @staticmethod
    async def update_medicine(
        db: AsyncSession,
        *,
        medicine: TreatmentPlanMedicine,
        data: dict[str, Any],
    ) -> TreatmentPlanMedicine:

        for key, value in data.items():

            if hasattr(
                medicine,
                key,
            ):
                setattr(
                    medicine,
                    key,
                    value,
                )

        medicine.total_price = (
            Decimal(
                medicine.quantity
            )
            * Decimal(
                medicine.unit_price
            )
        )

        await db.flush()

        await db.refresh(
            medicine
        )

        return medicine

    # ========================================================
    # MEDICINE - DELETE
    # ========================================================

    @staticmethod
    async def delete_medicine(
        db: AsyncSession,
        *,
        medicine: TreatmentPlanMedicine,
    ) -> None:

        await db.delete(
            medicine
        )

        await db.flush()

    # ========================================================
    # ITEM - CREATE
    # ========================================================

    @staticmethod
    async def create_item(
        db: AsyncSession,
        *,
        plan_id: int,
        data: dict[str, Any],
    ) -> TreatmentPlanItem:

        quantity = Decimal(
            str(
                data.get(
                    "quantity",
                    1,
                )
            )
        )

        unit_price = Decimal(
            str(
                data.get(
                    "unit_price",
                    0,
                )
            )
        )

        total_price = (
            quantity
            * unit_price
        )

        item = TreatmentPlanItem(
            treatment_plan_id=plan_id,
            **data,
            total_price=total_price,
        )

        db.add(
            item
        )

        await db.flush()

        await db.refresh(
            item
        )

        return item

    # ========================================================
    # ITEM - GET
    # ========================================================

    @staticmethod
    async def get_item(
        db: AsyncSession,
        *,
        item_id: int,
        plan_id: int | None = None,
    ) -> TreatmentPlanItem | None:

        statement = (
            select(
                TreatmentPlanItem
            )
            .where(
                TreatmentPlanItem.id
                == item_id
            )
        )

        if plan_id:
            statement = (
                statement.where(
                    TreatmentPlanItem
                    .treatment_plan_id
                    == plan_id
                )
            )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # ITEM - LIST
    # ========================================================

    @staticmethod
    async def list_items(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[TreatmentPlanItem]:

        result = await db.execute(
            select(
                TreatmentPlanItem
            )
            .where(
                TreatmentPlanItem
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanItem.id
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # ITEM - UPDATE
    # ========================================================

    @staticmethod
    async def update_item(
        db: AsyncSession,
        *,
        item: TreatmentPlanItem,
        data: dict[str, Any],
    ) -> TreatmentPlanItem:

        for key, value in data.items():

            if hasattr(
                item,
                key,
            ):
                setattr(
                    item,
                    key,
                    value,
                )

        item.total_price = (
            Decimal(
                item.quantity
            )
            * Decimal(
                item.unit_price
            )
        )

        await db.flush()

        await db.refresh(
            item
        )

        return item

    # ========================================================
    # ITEM - DELETE
    # ========================================================

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        *,
        item: TreatmentPlanItem,
    ) -> None:

        await db.delete(
            item
        )

        await db.flush()

    # ========================================================
    # SPECIALIST - ADD
    # ========================================================

    @staticmethod
    async def add_specialist(
        db: AsyncSession,
        *,
        plan_id: int,
        data: dict[str, Any],
    ) -> TreatmentPlanSpecialist:

        specialist = (
            TreatmentPlanSpecialist(
                treatment_plan_id=plan_id,
                **data,
            )
        )

        db.add(
            specialist
        )

        await db.flush()

        await db.refresh(
            specialist
        )

        return specialist

    # ========================================================
    # SPECIALIST - GET
    # ========================================================

    @staticmethod
    async def get_specialist_link(
        db: AsyncSession,
        *,
        specialist_link_id: int,
        plan_id: int | None = None,
    ) -> TreatmentPlanSpecialist | None:

        statement = (
            select(
                TreatmentPlanSpecialist
            )
            .where(
                TreatmentPlanSpecialist.id
                == specialist_link_id
            )
        )

        if plan_id:
            statement = (
                statement.where(
                    TreatmentPlanSpecialist
                    .treatment_plan_id
                    == plan_id
                )
            )

        result = await db.execute(
            statement
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # FIND SPECIALIST IN PLAN
    # ========================================================

    @staticmethod
    async def find_specialist_in_plan(
        db: AsyncSession,
        *,
        plan_id: int,
        specialist_id: int,
    ) -> TreatmentPlanSpecialist | None:

        result = await db.execute(
            select(
                TreatmentPlanSpecialist
            )
            .where(
                TreatmentPlanSpecialist
                .treatment_plan_id
                == plan_id,
                TreatmentPlanSpecialist
                .specialist_id
                == specialist_id,
            )
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # SPECIALIST - LIST
    # ========================================================

    @staticmethod
    async def list_specialists(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[TreatmentPlanSpecialist]:

        result = await db.execute(
            select(
                TreatmentPlanSpecialist
            )
            .where(
                TreatmentPlanSpecialist
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanSpecialist.id
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # SPECIALIST - DELETE
    # ========================================================

    @staticmethod
    async def delete_specialist(
        db: AsyncSession,
        *,
        specialist: TreatmentPlanSpecialist,
    ) -> None:

        await db.delete(
            specialist
        )

        await db.flush()

    # ========================================================
    # VERSION - CREATE
    # ========================================================

    @staticmethod
    async def create_version(
        db: AsyncSession,
        *,
        plan_id: int,
        version_number: int,
        created_by: int,
        status: str,
        snapshot: dict[str, Any],
        change_note: str | None = None,
    ) -> TreatmentPlanVersion:

        version = (
            TreatmentPlanVersion(
                treatment_plan_id=plan_id,
                version_number=version_number,
                created_by=created_by,
                status=status,
                snapshot=snapshot,
                change_note=change_note,
            )
        )

        db.add(
            version
        )

        await db.flush()

        await db.refresh(
            version
        )

        return version

    # ========================================================
    # VERSION - LIST
    # ========================================================

    @staticmethod
    async def list_versions(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[TreatmentPlanVersion]:

        result = await db.execute(
            select(
                TreatmentPlanVersion
            )
            .where(
                TreatmentPlanVersion
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanVersion
                .version_number
                .desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # VERSION - GET
    # ========================================================

    @staticmethod
    async def get_version(
        db: AsyncSession,
        *,
        plan_id: int,
        version_id: int,
    ) -> TreatmentPlanVersion | None:

        result = await db.execute(
            select(
                TreatmentPlanVersion
            )
            .where(
                TreatmentPlanVersion
                .treatment_plan_id
                == plan_id,
                TreatmentPlanVersion.id
                == version_id,
            )
        )

        return (
            result
            .scalars()
            .first()
        )

    # ========================================================
    # STATUS HISTORY - CREATE
    # ========================================================

    @staticmethod
    async def create_status_history(
        db: AsyncSession,
        *,
        plan_id: int,
        from_status: str | None,
        to_status: str,
        changed_by: int,
        reason: str | None = None,
        notes: str | None = None,
    ) -> TreatmentPlanStatusHistory:

        history = (
            TreatmentPlanStatusHistory(
                treatment_plan_id=plan_id,
                from_status=from_status,
                to_status=to_status,
                changed_by=changed_by,
                reason=reason,
                notes=notes,
            )
        )

        db.add(
            history
        )

        await db.flush()

        await db.refresh(
            history
        )

        return history

    # ========================================================
    # STATUS HISTORY - LIST
    # ========================================================

    @staticmethod
    async def list_status_history(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> list[
        TreatmentPlanStatusHistory
    ]:

        result = await db.execute(
            select(
                TreatmentPlanStatusHistory
            )
            .where(
                TreatmentPlanStatusHistory
                .treatment_plan_id
                == plan_id
            )
            .order_by(
                TreatmentPlanStatusHistory
                .id
                .desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # ========================================================
    # PRICING TOTALS
    # ========================================================

    @staticmethod
    async def calculate_totals(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> dict[str, Decimal]:

        # ----------------------------------------------------
        # Therapy total
        # ----------------------------------------------------

        therapy_result = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            TreatmentPlanTherapy
                            .total_price
                        ),
                        0,
                    )
                )
                .where(
                    TreatmentPlanTherapy
                    .treatment_plan_id
                    == plan_id
                )
            )
        )

        therapy_total = Decimal(
            str(
                therapy_result.scalar()
                or 0
            )
        )

        # ----------------------------------------------------
        # Medicine total
        # ----------------------------------------------------

        medicine_result = (
            await db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            TreatmentPlanMedicine
                            .total_price
                        ),
                        0,
                    )
                )
                .where(
                    TreatmentPlanMedicine
                    .treatment_plan_id
                    == plan_id
                )
            )
        )

        medicine_total = Decimal(
            str(
                medicine_result.scalar()
                or 0
            )
        )

        # ----------------------------------------------------
        # Generic service/item total
        # ----------------------------------------------------

        item_result = await db.execute(
    select(
        func.coalesce(
            func.sum(
                TreatmentPlanItem.total_price
            ),
            0,
        )
    )
    .where(
        TreatmentPlanItem.treatment_plan_id
        == plan_id,
        TreatmentPlanItem.item_type.in_(
            [
                "SERVICE",
                "PROCEDURE",
                "OTHER",
            ]
        ),
    )
)

        service_total = Decimal(
            str(
                item_result.scalar()
                or 0
            )
        )

        return {
            "therapy_total":
                therapy_total,

            "medicine_total":
                medicine_total,

            "service_total":
                service_total,
        }