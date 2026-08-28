from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.dependencies import require_permission
from app.modules.users.model import User

from app.modules.treatment_plans.schemas import (
    TreatmentPlanApprovalRequest,
    TreatmentPlanCancelRequest,
    TreatmentPlanCreate,
    TreatmentPlanDetailResponse,
    TreatmentPlanFinalizeRequest,
    TreatmentPlanItemCreate,
    TreatmentPlanItemResponse,
    TreatmentPlanItemUpdate,
    TreatmentPlanMedicineCreate,
    TreatmentPlanMedicineResponse,
    TreatmentPlanMedicineUpdate,
    TreatmentPlanModificationRequest,
    TreatmentPlanPricingResponse,
    TreatmentPlanResponse,
    TreatmentPlanRoomUpdate,
    TreatmentPlanSpecialistCreate,
    TreatmentPlanSpecialistResponse,
    TreatmentPlanStatusHistoryResponse,
    TreatmentPlanSubmitModificationRequest,
    TreatmentPlanSubmitRequest,
    TreatmentPlanSummaryResponse,
    TreatmentPlanTherapyCreate,
    TreatmentPlanTherapyResponse,
    TreatmentPlanTherapyUpdate,
    TreatmentPlanUpdate,
    TreatmentPlanVersionResponse,
)

from app.modules.treatment_plans.service import (
    TreatmentPlanService,
)


router = APIRouter(
    prefix="/treatment-plans",
    tags=["Treatment Plans"],
)


# ============================================================
# CREATE TREATMENT PLAN
#
# POST /api/v1/treatment-plans
# ============================================================


@router.post(
    "",
    response_model=TreatmentPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_treatment_plan(
    data: TreatmentPlanCreate,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.create"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.create_plan(
        db,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# MY TREATMENT PLANS
#
# GET /api/v1/treatment-plans/my
# ============================================================


@router.get(
    "/my",
    response_model=list[
        TreatmentPlanSummaryResponse
    ],
)
async def get_my_treatment_plans(
    status_value: str | None = Query(
        default=None,
        alias="status",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_permission(
            "treatment_plans.view_own"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_my_plans(
        db,
        user_id=current_user.id,
        status_value=status_value,
        page=page,
        limit=limit,
    )


# ============================================================
# GET FULL TREATMENT PLAN
#
# GET /api/v1/treatment-plans/{plan_id}
# ============================================================


@router.get(
    "/{plan_id}",
    response_model=TreatmentPlanDetailResponse,
)
async def get_treatment_plan(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.get_plan_details(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# UPDATE TREATMENT PLAN
#
# PATCH /api/v1/treatment-plans/{plan_id}
# ============================================================


@router.patch(
    "/{plan_id}",
    response_model=TreatmentPlanResponse,
)
async def update_treatment_plan(
    plan_id: int,
    data: TreatmentPlanUpdate,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.update"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.update_plan(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# DELETE DRAFT PLAN
#
# DELETE /api/v1/treatment-plans/{plan_id}
# ============================================================


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_treatment_plan(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.delete"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    await TreatmentPlanService.delete_plan(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# ============================================================
# THERAPIES - ADD
#
# POST /treatment-plans/{plan_id}/therapies
# ============================================================


@router.post(
    "/{plan_id}/therapies",
    response_model=TreatmentPlanTherapyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_treatment_plan_therapy(
    plan_id: int,
    data: TreatmentPlanTherapyCreate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_therapies.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.add_therapy(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# THERAPIES - LIST
# ============================================================


@router.get(
    "/{plan_id}/therapies",
    response_model=list[
        TreatmentPlanTherapyResponse
    ],
)
async def list_treatment_plan_therapies(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_therapies.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_therapies(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# THERAPIES - UPDATE
# ============================================================


@router.patch(
    "/{plan_id}/therapies/{therapy_item_id}",
    response_model=TreatmentPlanTherapyResponse,
)
async def update_treatment_plan_therapy(
    plan_id: int,
    therapy_item_id: int,
    data: TreatmentPlanTherapyUpdate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_therapies.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.update_therapy(
        db,
        plan_id=plan_id,
        therapy_item_id=therapy_item_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# THERAPIES - DELETE
# ============================================================


@router.delete(
    "/{plan_id}/therapies/{therapy_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_treatment_plan_therapy(
    plan_id: int,
    therapy_item_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_therapies.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    await TreatmentPlanService.delete_therapy(
        db,
        plan_id=plan_id,
        therapy_item_id=therapy_item_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# ============================================================
# MEDICINES - ADD
# ============================================================


@router.post(
    "/{plan_id}/medicines",
    response_model=TreatmentPlanMedicineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_treatment_plan_medicine(
    plan_id: int,
    data: TreatmentPlanMedicineCreate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_medicines.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.add_medicine(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# MEDICINES - LIST
# ============================================================


@router.get(
    "/{plan_id}/medicines",
    response_model=list[
        TreatmentPlanMedicineResponse
    ],
)
async def list_treatment_plan_medicines(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_medicines.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_medicines(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# MEDICINES - UPDATE
# ============================================================


@router.patch(
    "/{plan_id}/medicines/{medicine_item_id}",
    response_model=TreatmentPlanMedicineResponse,
)
async def update_treatment_plan_medicine(
    plan_id: int,
    medicine_item_id: int,
    data: TreatmentPlanMedicineUpdate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_medicines.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.update_medicine(
        db,
        plan_id=plan_id,
        medicine_item_id=medicine_item_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# MEDICINES - DELETE
# ============================================================


@router.delete(
    "/{plan_id}/medicines/{medicine_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_treatment_plan_medicine(
    plan_id: int,
    medicine_item_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_medicines.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    await TreatmentPlanService.delete_medicine(
        db,
        plan_id=plan_id,
        medicine_item_id=medicine_item_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# ============================================================
# GENERIC ITEMS - ADD
# ============================================================


@router.post(
    "/{plan_id}/items",
    response_model=TreatmentPlanItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_treatment_plan_item(
    plan_id: int,
    data: TreatmentPlanItemCreate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_items.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.add_item(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# ITEMS - LIST
# ============================================================


@router.get(
    "/{plan_id}/items",
    response_model=list[
        TreatmentPlanItemResponse
    ],
)
async def list_treatment_plan_items(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_items.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_items(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# ITEMS - UPDATE
# ============================================================


@router.patch(
    "/{plan_id}/items/{item_id}",
    response_model=TreatmentPlanItemResponse,
)
async def update_treatment_plan_item(
    plan_id: int,
    item_id: int,
    data: TreatmentPlanItemUpdate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_items.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.update_item(
        db,
        plan_id=plan_id,
        item_id=item_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# ITEMS - DELETE
# ============================================================


@router.delete(
    "/{plan_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_treatment_plan_item(
    plan_id: int,
    item_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_items.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    await TreatmentPlanService.delete_item(
        db,
        plan_id=plan_id,
        item_id=item_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# ============================================================
# ROOM / STAY RECOMMENDATION
#
# PUT /treatment-plans/{plan_id}/room
# ============================================================


@router.put(
    "/{plan_id}/room",
    response_model=TreatmentPlanResponse,
)
async def update_treatment_plan_room(
    plan_id: int,
    data: TreatmentPlanRoomUpdate,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.update"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.update_room(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# SPECIALIST COLLABORATION - ADD
# ============================================================


@router.post(
    "/{plan_id}/specialists",
    response_model=TreatmentPlanSpecialistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_treatment_plan_specialist(
    plan_id: int,
    data: TreatmentPlanSpecialistCreate,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_specialists.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.add_specialist(
        db,
        plan_id=plan_id,
        data=data,
        user_id=current_user.id,
    )


# ============================================================
# SPECIALIST COLLABORATION - LIST
# ============================================================


@router.get(
    "/{plan_id}/specialists",
    response_model=list[
        TreatmentPlanSpecialistResponse
    ],
)
async def list_treatment_plan_specialists(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_specialists.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_specialists(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# SPECIALIST COLLABORATION - REMOVE
# ============================================================


@router.delete(
    "/{plan_id}/specialists/{specialist_link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_treatment_plan_specialist(
    plan_id: int,
    specialist_link_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_specialists.manage"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    await TreatmentPlanService.remove_specialist(
        db,
        plan_id=plan_id,
        specialist_link_id=specialist_link_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


# ============================================================
# CALCULATE PRICE
#
# POST /treatment-plans/{plan_id}/calculate
# ============================================================


@router.post(
    "/{plan_id}/calculate",
    response_model=TreatmentPlanPricingResponse,
)
async def calculate_treatment_plan_price(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_pricing.calculate"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.calculate_pricing(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# SUBMIT PLAN
#
# DRAFT / MODIFIED → SUBMITTED
# ============================================================


@router.post(
    "/{plan_id}/submit",
    response_model=TreatmentPlanResponse,
)
async def submit_treatment_plan(
    plan_id: int,
    data: TreatmentPlanSubmitRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.submit"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.submit_plan(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        submission_note=data.submission_note,
    )


# ============================================================
# START REVIEW
#
# SUBMITTED → UNDER_REVIEW
# ============================================================


@router.post(
    "/{plan_id}/start-review",
    response_model=TreatmentPlanResponse,
)
async def start_treatment_plan_review(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.review"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.start_review(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# REQUEST MODIFICATION
#
# UNDER_REVIEW → MODIFICATION_REQUIRED
# ============================================================


@router.post(
    "/{plan_id}/request-modification",
    response_model=TreatmentPlanResponse,
)
async def request_treatment_plan_modification(
    plan_id: int,
    data: TreatmentPlanModificationRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.review"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.request_modification(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        reason=data.reason,
        comments=data.comments,
    )


# ============================================================
# MARK MODIFIED
#
# MODIFICATION_REQUIRED → MODIFIED
# ============================================================


@router.post(
    "/{plan_id}/submit-modification",
    response_model=TreatmentPlanResponse,
)
async def submit_treatment_plan_modification(
    plan_id: int,
    data: TreatmentPlanSubmitModificationRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.update"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.mark_modified(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        note=data.modification_note,
    )


# ============================================================
# APPROVE PLAN
#
# UNDER_REVIEW → APPROVED
# ============================================================


@router.post(
    "/{plan_id}/approve",
    response_model=TreatmentPlanResponse,
)
async def approve_treatment_plan(
    plan_id: int,
    data: TreatmentPlanApprovalRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.approve"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.approve(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        approval_note=data.approval_note,
    )


# ============================================================
# FINALIZE PLAN
#
# APPROVED → FINALIZED
# ============================================================


@router.post(
    "/{plan_id}/finalize",
    response_model=TreatmentPlanResponse,
)
async def finalize_treatment_plan(
    plan_id: int,
    data: TreatmentPlanFinalizeRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.finalize"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.finalize(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        finalization_note=data.finalization_note,
    )


# ============================================================
# CANCEL PLAN
# ============================================================


@router.post(
    "/{plan_id}/cancel",
    response_model=TreatmentPlanResponse,
)
async def cancel_treatment_plan(
    plan_id: int,
    data: TreatmentPlanCancelRequest,
    current_user: User = Depends(
        require_permission(
            "treatment_plans.cancel"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.cancel(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
        reason=data.reason,
        notes=data.notes,
    )


# ============================================================
# VERSION HISTORY
# ============================================================


@router.get(
    "/{plan_id}/versions",
    response_model=list[
        TreatmentPlanVersionResponse
    ],
)
async def get_treatment_plan_versions(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_versions.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_versions(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )


# ============================================================
# STATUS HISTORY
# ============================================================


@router.get(
    "/{plan_id}/status-history",
    response_model=list[
        TreatmentPlanStatusHistoryResponse
    ],
)
async def get_treatment_plan_status_history(
    plan_id: int,
    current_user: User = Depends(
        require_permission(
            "treatment_plan_status_history.view"
        )
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    return await TreatmentPlanService.list_status_history(
        db,
        plan_id=plan_id,
        user_id=current_user.id,
    )