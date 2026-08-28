from datetime import (
    datetime,
    timezone,
)
from decimal import Decimal
from typing import Any

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.treatment_plans.models import (
    TreatmentPlan,
    TreatmentPlanItem,
    TreatmentPlanMedicine,
    TreatmentPlanSpecialist,
    TreatmentPlanTherapy,
)
from app.modules.treatment_plans.repository import (
    TreatmentPlanRepository,
)
from app.modules.treatment_plans.schemas import (
    TreatmentPlanCreate,
    TreatmentPlanItemCreate,
    TreatmentPlanItemUpdate,
    TreatmentPlanMedicineCreate,
    TreatmentPlanMedicineUpdate,
    TreatmentPlanRoomUpdate,
    TreatmentPlanSpecialistCreate,
    TreatmentPlanTherapyCreate,
    TreatmentPlanTherapyUpdate,
    TreatmentPlanUpdate,
)


# ============================================================
# STATUS ENGINE
# ============================================================

ALLOWED_TRANSITIONS = {
    "DRAFT": {
        "SUBMITTED",
        "CANCELLED",
    },

    "SUBMITTED": {
        "UNDER_REVIEW",
        "CANCELLED",
    },

    "UNDER_REVIEW": {
        "APPROVED",
        "MODIFICATION_REQUIRED",
        "CANCELLED",
    },

    "MODIFICATION_REQUIRED": {
        "MODIFIED",
        "CANCELLED",
    },

    "MODIFIED": {
        "SUBMITTED",
        "CANCELLED",
    },

    "APPROVED": {
        "FINALIZED",
    },

    "FINALIZED": set(),

    "CANCELLED": set(),
}


# ============================================================
# EDITABLE STATUSES
# ============================================================

EDITABLE_STATUSES = {
    "DRAFT",
    "MODIFICATION_REQUIRED",
    "MODIFIED",
}


# ============================================================
# UTILITY
# ============================================================

def utcnow() -> datetime:
    """
    MySQL DateTime columns in the current model
    are timezone-naive.

    Store UTC consistently.
    """

    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def decimal_value(
    value: Any,
) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(
        str(value)
    )


def json_value(
    value: Any,
):
    """
    Convert values into JSON-safe forms
    for treatment_plan_versions.snapshot.
    """

    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    return value


# ============================================================
# SERVICE
# ============================================================


class TreatmentPlanService:

    # ========================================================
    # REQUIRE PLAN
    # ========================================================

    @staticmethod
    async def require_plan(
        db: AsyncSession,
        *,
        plan_id: int,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanRepository.get_plan(
                db,
                plan_id=plan_id,
            )
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment plan not found.",
            )

        return plan

    # ========================================================
    # REQUIRE EDITABLE
    # ========================================================

    @staticmethod
    def require_editable(
        plan: TreatmentPlan,
    ) -> None:

        if (
            plan.status
            not in EDITABLE_STATUSES
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Treatment plan cannot be edited "
                    f"while status is {plan.status}."
                ),
            )

    # ========================================================
    # REQUIRE PLAN ACCESS
    #
    # Creator OR collaborating specialist.
    # ========================================================

    @staticmethod
    async def require_plan_access(
        db: AsyncSession,
        *,
        plan: TreatmentPlan,
        user_id: int,
    ) -> None:

        if (
            int(plan.created_by)
            == int(user_id)
        ):
            return

        specialist = (
            await TreatmentPlanRepository
            .find_specialist_in_plan(
                db,
                plan_id=plan.id,
                specialist_id=user_id,
            )
        )

        if specialist:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access to this "
                "treatment plan."
            ),
        )

    # ========================================================
    # CREATE PLAN
    # ========================================================

    @staticmethod
    async def create_plan(
        db: AsyncSession,
        *,
        data: TreatmentPlanCreate,
        user_id: int,
    ) -> TreatmentPlan:

        try:
            plan = (
                await TreatmentPlanRepository.create_plan(
                    db,
                    data=data.model_dump(
                        exclude_none=True
                    ),
                    created_by=user_id,
                )
            )

            # ------------------------------------------------
            # Initial status history
            # ------------------------------------------------

            await TreatmentPlanRepository.create_status_history(
                db,
                plan_id=plan.id,
                from_status=None,
                to_status="DRAFT",
                changed_by=user_id,
                reason="Treatment plan created",
            )

            # ------------------------------------------------
            # Automatically add creator as primary specialist
            # ------------------------------------------------

            existing = (
                await TreatmentPlanRepository
                .find_specialist_in_plan(
                    db,
                    plan_id=plan.id,
                    specialist_id=user_id,
                )
            )

            if not existing:
                await TreatmentPlanRepository.add_specialist(
                    db,
                    plan_id=plan.id,
                    data={
                        "specialist_id":
                            user_id,

                        "role":
                            "PRIMARY_SPECIALIST",

                        "is_primary":
                            True,

                        "status":
                            "ACTIVE",
                    },
                )

            await db.commit()

            await db.refresh(
                plan
            )

            return plan

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # GET PLAN
    # ========================================================

    @staticmethod
    async def get_plan(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return plan

    # ========================================================
    # GET FULL TREATMENT PLAN DETAILS
    #
    # IMPORTANT:
    # Return the SQLAlchemy TreatmentPlan object.
    # FastAPI/Pydantic handles serialization through
    # TreatmentPlanDetailResponse(from_attributes=True).
    #
    # Do NOT return a dict here because internal service
    # methods such as submit_plan() require plan.status,
    # plan.plan_title, plan.current_version, etc.
    # ========================================================

    @staticmethod
    async def get_plan_details(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanRepository
            .get_plan_with_details(
                db,
                plan_id=plan_id,
            )
        )

        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment plan not found.",
            )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return plan

    # ========================================================
    # LIST MY PLANS
    # ========================================================

    @staticmethod
    async def list_my_plans(
        db: AsyncSession,
        *,
        user_id: int,
        status_value: str | None = None,
        page: int = 1,
        limit: int = 100,
    ):

        return (
            await TreatmentPlanRepository.list_my_plans(
                db,
                user_id=user_id,
                status=status_value,
                page=page,
                limit=limit,
            )
        )

    # ========================================================
    # UPDATE PLAN
    # ========================================================

    @staticmethod
    async def update_plan(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanUpdate,
        user_id: int,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        payload = data.model_dump(
            exclude_unset=True
        )

        try:
            plan = (
                await TreatmentPlanRepository.update_plan(
                    db,
                    plan=plan,
                    data=payload,
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                plan
            )

            return plan

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # DELETE DRAFT
    # ========================================================

    @staticmethod
    async def delete_plan(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ) -> None:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        if (
            int(plan.created_by)
            != int(user_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only the treatment-plan creator "
                    "can delete this plan."
                ),
            )

        if plan.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only DRAFT treatment plans "
                    "can be deleted."
                ),
            )

        try:
            await TreatmentPlanRepository.delete_plan(
                db,
                plan=plan,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # THERAPY - ADD
    # ========================================================

    @staticmethod
    async def add_therapy(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanTherapyCreate,
        user_id: int,
    ) -> TreatmentPlanTherapy:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        try:
            therapy = (
                await TreatmentPlanRepository.create_therapy(
                    db,
                    plan_id=plan.id,
                    data=data.model_dump(
                        exclude_none=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                therapy
            )

            return therapy

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # THERAPY - UPDATE
    # ========================================================

    @staticmethod
    async def update_therapy(
        db: AsyncSession,
        *,
        plan_id: int,
        therapy_item_id: int,
        data: TreatmentPlanTherapyUpdate,
        user_id: int,
    ) -> TreatmentPlanTherapy:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        therapy = (
            await TreatmentPlanRepository.get_therapy(
                db,
                therapy_item_id=therapy_item_id,
                plan_id=plan_id,
            )
        )

        if not therapy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan therapy not found.",
            )

        try:
            therapy = (
                await TreatmentPlanRepository.update_therapy(
                    db,
                    therapy=therapy,
                    data=data.model_dump(
                        exclude_unset=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                therapy
            )

            return therapy

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # THERAPY - DELETE
    # ========================================================

    @staticmethod
    async def delete_therapy(
        db: AsyncSession,
        *,
        plan_id: int,
        therapy_item_id: int,
        user_id: int,
    ) -> None:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        therapy = (
            await TreatmentPlanRepository.get_therapy(
                db,
                therapy_item_id=therapy_item_id,
                plan_id=plan_id,
            )
        )

        if not therapy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan therapy not found.",
            )

        try:
            await TreatmentPlanRepository.delete_therapy(
                db,
                therapy=therapy,
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # MEDICINE - ADD
    # ========================================================

    @staticmethod
    async def add_medicine(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanMedicineCreate,
        user_id: int,
    ) -> TreatmentPlanMedicine:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        try:
            medicine = (
                await TreatmentPlanRepository.create_medicine(
                    db,
                    plan_id=plan.id,
                    data=data.model_dump(
                        exclude_none=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                medicine
            )

            return medicine

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # MEDICINE - UPDATE
    # ========================================================

    @staticmethod
    async def update_medicine(
        db: AsyncSession,
        *,
        plan_id: int,
        medicine_item_id: int,
        data: TreatmentPlanMedicineUpdate,
        user_id: int,
    ) -> TreatmentPlanMedicine:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        medicine = (
            await TreatmentPlanRepository.get_medicine(
                db,
                medicine_item_id=medicine_item_id,
                plan_id=plan_id,
            )
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan medicine not found.",
            )

        try:
            medicine = (
                await TreatmentPlanRepository.update_medicine(
                    db,
                    medicine=medicine,
                    data=data.model_dump(
                        exclude_unset=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                medicine
            )

            return medicine

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # MEDICINE - DELETE
    # ========================================================

    @staticmethod
    async def delete_medicine(
        db: AsyncSession,
        *,
        plan_id: int,
        medicine_item_id: int,
        user_id: int,
    ) -> None:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        medicine = (
            await TreatmentPlanRepository.get_medicine(
                db,
                medicine_item_id=medicine_item_id,
                plan_id=plan_id,
            )
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan medicine not found.",
            )

        try:
            await TreatmentPlanRepository.delete_medicine(
                db,
                medicine=medicine,
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # GENERIC ITEM - ADD
    # ========================================================

    @staticmethod
    async def add_item(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanItemCreate,
        user_id: int,
    ) -> TreatmentPlanItem:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        try:
            item = (
                await TreatmentPlanRepository.create_item(
                    db,
                    plan_id=plan.id,
                    data=data.model_dump(
                        exclude_none=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                item
            )

            return item

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # GENERIC ITEM - UPDATE
    # ========================================================

    @staticmethod
    async def update_item(
        db: AsyncSession,
        *,
        plan_id: int,
        item_id: int,
        data: TreatmentPlanItemUpdate,
        user_id: int,
    ) -> TreatmentPlanItem:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        item = (
            await TreatmentPlanRepository.get_item(
                db,
                item_id=item_id,
                plan_id=plan_id,
            )
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan item not found.",
            )

        try:
            item = (
                await TreatmentPlanRepository.update_item(
                    db,
                    item=item,
                    data=data.model_dump(
                        exclude_unset=True
                    ),
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                item
            )

            return item

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # GENERIC ITEM - DELETE
    # ========================================================

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        *,
        plan_id: int,
        item_id: int,
        user_id: int,
    ) -> None:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        item = (
            await TreatmentPlanRepository.get_item(
                db,
                item_id=item_id,
                plan_id=plan_id,
            )
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment-plan item not found.",
            )

        try:
            await TreatmentPlanRepository.delete_item(
                db,
                item=item,
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # ROOM / STAY RECOMMENDATION
    # ========================================================

    @staticmethod
    async def update_room(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanRoomUpdate,
        user_id: int,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        payload = {
            "room_type_id":
                data.room_type_id,

            "room_name":
                data.room_name,

            "stay_duration_days":
                data.stay_duration_days,

            "room_daily_rate":
                data.daily_rate,
        }

        try:
            plan = (
                await TreatmentPlanRepository.update_plan(
                    db,
                    plan=plan,
                    data=payload,
                )
            )

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            await db.commit()

            await db.refresh(
                plan
            )

            return plan

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # SPECIALIST COLLABORATION - ADD
    # ========================================================

    @staticmethod
    async def add_specialist(
        db: AsyncSession,
        *,
        plan_id: int,
        data: TreatmentPlanSpecialistCreate,
        user_id: int,
    ) -> TreatmentPlanSpecialist:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        existing = (
            await TreatmentPlanRepository
            .find_specialist_in_plan(
                db,
                plan_id=plan_id,
                specialist_id=data.specialist_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Specialist is already attached "
                    "to this treatment plan."
                ),
            )

        try:
            specialist = (
                await TreatmentPlanRepository.add_specialist(
                    db,
                    plan_id=plan_id,
                    data=data.model_dump(
                        exclude_none=True
                    ),
                )
            )

            await db.commit()

            await db.refresh(
                specialist
            )

            return specialist

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # SPECIALIST COLLABORATION - REMOVE
    # ========================================================

    @staticmethod
    async def remove_specialist(
        db: AsyncSession,
        *,
        plan_id: int,
        specialist_link_id: int,
        user_id: int,
    ) -> None:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        TreatmentPlanService.require_editable(
            plan
        )

        specialist = (
            await TreatmentPlanRepository.get_specialist_link(
                db,
                specialist_link_id=specialist_link_id,
                plan_id=plan_id,
            )
        )

        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collaborating specialist not found.",
            )

        if specialist.is_primary:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Primary specialist cannot be removed."
                ),
            )

        try:
            await TreatmentPlanRepository.delete_specialist(
                db,
                specialist=specialist,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise
    # ========================================================
    # LIST THERAPIES
    # ========================================================

    @staticmethod
    async def list_therapies(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):
        plan = await TreatmentPlanService.require_plan(
            db,
            plan_id=plan_id,
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return await TreatmentPlanRepository.list_therapies(
            db,
            plan_id=plan_id,
        )

    # ========================================================
    # LIST MEDICINES
    # ========================================================

    @staticmethod
    async def list_medicines(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):
        plan = await TreatmentPlanService.require_plan(
            db,
            plan_id=plan_id,
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return await TreatmentPlanRepository.list_medicines(
            db,
            plan_id=plan_id,
        )

    # ========================================================
    # LIST ITEMS
    # ========================================================

    @staticmethod
    async def list_items(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):
        plan = await TreatmentPlanService.require_plan(
            db,
            plan_id=plan_id,
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return await TreatmentPlanRepository.list_items(
            db,
            plan_id=plan_id,
        )

    # ========================================================
    # LIST SPECIALISTS
    # ========================================================

    @staticmethod
    async def list_specialists(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):
        plan = await TreatmentPlanService.require_plan(
            db,
            plan_id=plan_id,
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return await TreatmentPlanRepository.list_specialists(
            db,
            plan_id=plan_id,
        )
    # ========================================================
    # PRICE CALCULATION
    # ========================================================

    @staticmethod
    async def calculate_pricing(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ) -> dict[str, Any]:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        try:
            pricing = (
                await TreatmentPlanService._recalculate_pricing(
                    db,
                    plan=plan,
                )
            )

            await db.commit()

            return pricing

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # INTERNAL PRICE CALCULATION
    # ========================================================

    @staticmethod
    async def _recalculate_pricing(
        db: AsyncSession,
        *,
        plan: TreatmentPlan,
    ) -> dict[str, Decimal]:

        totals = (
            await TreatmentPlanRepository.calculate_totals(
                db,
                plan_id=plan.id,
            )
        )

        therapy_total = decimal_value(
            totals.get(
                "therapy_total"
            )
        )

        medicine_total = decimal_value(
            totals.get(
                "medicine_total"
            )
        )

        service_total = decimal_value(
            totals.get(
                "service_total"
            )
        )

        room_rate = decimal_value(
            plan.room_daily_rate
        )

        stay_days = Decimal(
            str(
                plan.stay_duration_days
                or 0
            )
        )

        room_total = (
            room_rate
            * stay_days
        )

        subtotal = (
            therapy_total
            + medicine_total
            + service_total
            + room_total
        )

        discount_amount = decimal_value(
            plan.discount_amount
        )

        tax_amount = decimal_value(
            plan.tax_amount
        )

        grand_total = (
            subtotal
            - discount_amount
            + tax_amount
        )

        if grand_total < 0:
            grand_total = (
                Decimal("0.00")
            )

        plan.therapy_total = (
            therapy_total
        )

        plan.medicine_total = (
            medicine_total
        )

        plan.service_total = (
            service_total
        )

        plan.room_total = (
            room_total
        )

        plan.subtotal = (
            subtotal
        )

        plan.grand_total = (
            grand_total
        )

        await db.flush()

        return {
            "treatment_plan_id":
                plan.id,

            "therapy_total":
                therapy_total,

            "medicine_total":
                medicine_total,

            "room_total":
                room_total,

            "service_total":
                service_total,

            "subtotal":
                subtotal,

            "discount_amount":
                discount_amount,

            "tax_amount":
                tax_amount,

            "grand_total":
                grand_total,
        }

    # ========================================================
    # STATUS TRANSITION
    # ========================================================

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        *,
        plan_id: int,
        new_status: str,
        user_id: int,
        reason: str | None = None,
        notes: str | None = None,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        # ----------------------------------------------------
        # ACCESS CHECK
        # ----------------------------------------------------

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        current_status = plan.status

        if new_status == current_status:
            return plan

        allowed = ALLOWED_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Invalid treatment-plan status "
                    f"transition: "
                    f"{current_status} -> {new_status}"
                ),
            )

        try:
            plan.status = new_status

            if new_status == "SUBMITTED":
                plan.submitted_at = utcnow()

            if new_status == "FINALIZED":
                plan.finalized_at = utcnow()

            await TreatmentPlanRepository.create_status_history(
                db,
                plan_id=plan.id,
                from_status=current_status,
                to_status=new_status,
                changed_by=user_id,
                reason=reason,
                notes=notes,
            )

            await db.flush()

            await db.commit()

            await db.refresh(
                plan
            )

            return plan

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # SUBMIT PLAN
    #
    # DRAFT / MODIFIED → SUBMITTED
    # Creates immutable version snapshot.
    # ========================================================

    @staticmethod
    async def submit_plan(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        submission_note: str | None = None,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService
            .get_plan_details(
                db,
                plan_id=plan_id,
                user_id=user_id,
            )
        )

        if (
            plan.status
            not in {
                "DRAFT",
                "MODIFIED",
            }
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only DRAFT or MODIFIED "
                    "plans can be submitted."
                ),
            )

        # ----------------------------------------------------
        # Minimum clinical content required before submit
        # ----------------------------------------------------

        if not plan.plan_title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Plan title is required.",
            )

        if not plan.clinical_summary:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Clinical summary is required before submission.",
            )

        if not plan.treatment_goal:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Treatment goal is required before submission.",
            )

        try:
            # ------------------------------------------------
            # Calculate final current pricing
            # ------------------------------------------------

            await TreatmentPlanService._recalculate_pricing(
                db,
                plan=plan,
            )

            old_status = (
                plan.status
            )

            # ------------------------------------------------
            # Determine next version
            # ------------------------------------------------

            versions = (
                await TreatmentPlanRepository.list_versions(
                    db,
                    plan_id=plan.id,
                )
            )

            next_version = (
                max(
                    [
                        item.version_number
                        for item in versions
                    ],
                    default=0,
                )
                + 1
            )

            plan.status = (
                "SUBMITTED"
            )

            plan.current_version = (
                next_version
            )

            plan.submitted_at = (
                utcnow()
            )

            await db.flush()

            # ------------------------------------------------
            # Reload complete state for snapshot
            # ------------------------------------------------

            detailed_plan = (
                await TreatmentPlanRepository
                .get_plan_with_details(
                    db,
                    plan_id=plan.id,
                )
            )

            if detailed_plan is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Treatment plan not found while creating version snapshot.",
                )

            snapshot = (
                TreatmentPlanService
                .build_snapshot(
                    detailed_plan
                )
            )

            # ------------------------------------------------
            # Create version
            # ------------------------------------------------

            await TreatmentPlanRepository.create_version(
                db,
                plan_id=plan.id,
                version_number=next_version,
                created_by=user_id,
                status="SUBMITTED",
                snapshot=snapshot,
                change_note=submission_note,
            )

            # ------------------------------------------------
            # Status history
            # ------------------------------------------------

            await TreatmentPlanRepository.create_status_history(
                db,
                plan_id=plan.id,
                from_status=old_status,
                to_status="SUBMITTED",
                changed_by=user_id,
                reason=(
                    submission_note
                    or
                    "Treatment plan submitted"
                ),
            )

            await db.commit()

            await db.refresh(
                plan
            )

            return plan

        except Exception:
            await db.rollback()
            raise

    # ========================================================
    # START REVIEW
    # ========================================================

    @staticmethod
    async def start_review(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        reason: str | None = None,
    ) -> TreatmentPlan:

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="UNDER_REVIEW",
                user_id=user_id,
                reason=(
                    reason
                    or
                    "Treatment plan review started"
                ),
            )
        )

    # ========================================================
    # REQUEST MODIFICATION
    # ========================================================

    @staticmethod
    async def request_modification(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        reason: str,
        comments: str | None = None,
    ) -> TreatmentPlan:

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="MODIFICATION_REQUIRED",
                user_id=user_id,
                reason=reason,
                notes=comments,
            )
        )

    # ========================================================
    # MARK MODIFIED
    #
    # MODIFICATION_REQUIRED → MODIFIED
    # ========================================================

    @staticmethod
    async def mark_modified(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        note: str | None = None,
    ) -> TreatmentPlan:

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="MODIFIED",
                user_id=user_id,
                reason=(
                    note
                    or
                    "Requested treatment-plan changes completed"
                ),
            )
        )

    # ========================================================
    # APPROVE
    # ========================================================

    @staticmethod
    async def approve(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        approval_note: str | None = None,
    ) -> TreatmentPlan:

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="APPROVED",
                user_id=user_id,
                reason=(
                    approval_note
                    or
                    "Treatment plan approved"
                ),
            )
        )

    # ========================================================
    # FINALIZE
    # ========================================================

    @staticmethod
    async def finalize(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        finalization_note: str | None = None,
    ) -> TreatmentPlan:

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="FINALIZED",
                user_id=user_id,
                reason=(
                    finalization_note
                    or
                    "Treatment plan finalized"
                ),
            )
        )

    # ========================================================
    # CANCEL
    # ========================================================

    @staticmethod
    async def cancel(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
        reason: str,
        notes: str | None = None,
    ) -> TreatmentPlan:

        return (
            await TreatmentPlanService.transition_status(
                db,
                plan_id=plan_id,
                new_status="CANCELLED",
                user_id=user_id,
                reason=reason,
                notes=notes,
            )
        )

    # ========================================================
    # VERSION HISTORY
    # ========================================================

    @staticmethod
    async def list_versions(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return (
            await TreatmentPlanRepository.list_versions(
                db,
                plan_id=plan_id,
            )
        )

    # ========================================================
    # STATUS HISTORY
    # ========================================================

    @staticmethod
    async def list_status_history(
        db: AsyncSession,
        *,
        plan_id: int,
        user_id: int,
    ):

        plan = (
            await TreatmentPlanService.require_plan(
                db,
                plan_id=plan_id,
            )
        )

        await TreatmentPlanService.require_plan_access(
            db,
            plan=plan,
            user_id=user_id,
        )

        return (
            await TreatmentPlanRepository.list_status_history(
                db,
                plan_id=plan_id,
            )
        )

    # ========================================================
    # SNAPSHOT
    # ========================================================

    @staticmethod
    def build_snapshot(
        plan: TreatmentPlan,
    ) -> dict[str, Any]:

        return {
            "id":
                plan.id,

            "patient_id":
                plan.patient_id,

            "consultation_id":
                plan.consultation_id,

            "referral_id":
                plan.referral_id,

            "created_by":
                plan.created_by,

            "plan_title":
                plan.plan_title,

            "clinical_summary":
                plan.clinical_summary,

            "treatment_goal":
                plan.treatment_goal,

            "treatment_duration_days":
                plan.treatment_duration_days,

            "stay_duration_days":
                plan.stay_duration_days,

            "room": {
                "room_type_id":
                    plan.room_type_id,

                "room_name":
                    plan.room_name,

                "daily_rate":
                    json_value(
                        plan.room_daily_rate
                    ),

                "room_total":
                    json_value(
                        plan.room_total
                    ),
            },

            "pricing": {
                "therapy_total":
                    json_value(
                        plan.therapy_total
                    ),

                "medicine_total":
                    json_value(
                        plan.medicine_total
                    ),

                "service_total":
                    json_value(
                        plan.service_total
                    ),

                "room_total":
                    json_value(
                        plan.room_total
                    ),

                "subtotal":
                    json_value(
                        plan.subtotal
                    ),

                "discount_amount":
                    json_value(
                        plan.discount_amount
                    ),

                "tax_amount":
                    json_value(
                        plan.tax_amount
                    ),

                "grand_total":
                    json_value(
                        plan.grand_total
                    ),
            },

            "therapies": [
                {
                    "id":
                        item.id,

                    "therapy_id":
                        item.therapy_id,

                    "therapy_name":
                        item.therapy_name,

                    "sessions":
                        item.sessions,

                    "frequency":
                        item.frequency,

                    "duration_days":
                        item.duration_days,

                    "unit_price":
                        json_value(
                            item.unit_price
                        ),

                    "total_price":
                        json_value(
                            item.total_price
                        ),

                    "instructions":
                        item.instructions,

                    "notes":
                        item.notes,
                }
                for item
                in plan.therapies
            ],

            "medicines": [
                {
                    "id":
                        item.id,

                    "medicine_id":
                        item.medicine_id,

                    "medicine_name":
                        item.medicine_name,

                    "dosage":
                        item.dosage,

                    "frequency":
                        item.frequency,

                    "route":
                        item.route,

                    "duration_days":
                        item.duration_days,

                    "quantity":
                        json_value(
                            item.quantity
                        ),

                    "unit_price":
                        json_value(
                            item.unit_price
                        ),

                    "total_price":
                        json_value(
                            item.total_price
                        ),

                    "instructions":
                        item.instructions,

                    "notes":
                        item.notes,
                }
                for item
                in plan.medicines
            ],

            "items": [
                {
                    "id":
                        item.id,

                    "item_type":
                        item.item_type,

                    "reference_id":
                        item.reference_id,

                    "item_name":
                        item.item_name,

                    "description":
                        item.description,

                    "quantity":
                        json_value(
                            item.quantity
                        ),

                    "unit_price":
                        json_value(
                            item.unit_price
                        ),

                    "total_price":
                        json_value(
                            item.total_price
                        ),

                    "notes":
                        item.notes,
                }
                for item
                in plan.items
            ],

            "specialists": [
                {
                    "id":
                        item.id,

                    "specialist_id":
                        item.specialist_id,

                    "role":
                        item.role,

                    "specialty":
                        item.specialty,

                    "is_primary":
                        item.is_primary,

                    "status":
                        item.status,

                    "notes":
                        item.notes,
                }
                for item
                in plan.specialists
            ],

            "notes":
                plan.notes,

            "status":
                plan.status,

            "current_version":
                plan.current_version,
        }