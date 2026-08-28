from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)


# ============================================================
# STATUS TYPES
# ============================================================

TreatmentPlanStatus = Literal[
    "DRAFT",
    "SUBMITTED",
    "UNDER_REVIEW",
    "APPROVED",
    "MODIFICATION_REQUIRED",
    "MODIFIED",
    "FINALIZED",
    "CANCELLED",
]


TreatmentPlanItemType = Literal[
    "THERAPY",
    "MEDICINE",
    "ROOM",
    "SERVICE",
    "PROCEDURE",
    "OTHER",
]


TreatmentPlanSpecialistRole = Literal[
    "PRIMARY_SPECIALIST",
    "CONSULTING_SPECIALIST",
    "REVIEWING_SPECIALIST",
]


# ============================================================
# TREATMENT PLAN - CREATE
# ============================================================


class TreatmentPlanCreate(BaseModel):

    patient_id: int = Field(
        gt=0,
    )

    consultation_id: int | None = Field(
        default=None,
        gt=0,
    )

    referral_id: int | None = Field(
        default=None,
        gt=0,
    )

    plan_title: str = Field(
        min_length=1,
        max_length=255,
    )

    clinical_summary: str | None = None

    treatment_goal: str | None = None

    treatment_duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    stay_duration_days: int | None = Field(
        default=None,
        ge=0,
        le=3650,
    )

    room_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    room_name: str | None = Field(
        default=None,
        max_length=150,
    )

    room_daily_rate: Decimal | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = None


# ============================================================
# TREATMENT PLAN - UPDATE
# ============================================================


class TreatmentPlanUpdate(BaseModel):

    plan_title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    clinical_summary: str | None = None

    treatment_goal: str | None = None

    treatment_duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    stay_duration_days: int | None = Field(
        default=None,
        ge=0,
        le=3650,
    )

    room_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    room_name: str | None = Field(
        default=None,
        max_length=150,
    )

    room_daily_rate: Decimal | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = None


# ============================================================
# TREATMENT PLAN - SUMMARY RESPONSE
# ============================================================


class TreatmentPlanSummaryResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    patient_id: int

    consultation_id: int | None = None

    referral_id: int | None = None

    created_by: int

    plan_title: str

    status: TreatmentPlanStatus

    treatment_duration_days: int | None = None

    stay_duration_days: int | None = None

    grand_total: Decimal = Decimal("0.00")

    current_version: int


# ============================================================
# TREATMENT PLAN - STANDARD RESPONSE
# ============================================================


class TreatmentPlanResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    patient_id: int

    consultation_id: int | None = None

    referral_id: int | None = None

    created_by: int

    plan_title: str

    clinical_summary: str | None = None

    treatment_goal: str | None = None

    treatment_duration_days: int | None = None

    stay_duration_days: int | None = None

    # --------------------------------------------------------
    # ROOM FLAT FIELDS
    # --------------------------------------------------------

    room_type_id: int | None = None

    room_name: str | None = None

    room_daily_rate: Decimal | None = None

    # --------------------------------------------------------
    # PRICING FLAT FIELDS
    # --------------------------------------------------------

    therapy_total: Decimal = Decimal("0.00")

    medicine_total: Decimal = Decimal("0.00")

    room_total: Decimal = Decimal("0.00")

    service_total: Decimal = Decimal("0.00")

    subtotal: Decimal = Decimal("0.00")

    discount_amount: Decimal = Decimal("0.00")

    tax_amount: Decimal = Decimal("0.00")

    grand_total: Decimal = Decimal("0.00")

    # --------------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------------

    status: TreatmentPlanStatus

    current_version: int

    notes: str | None = None

    submitted_at: datetime | None = None

    finalized_at: datetime | None = None


# ============================================================
# TREATMENT PLAN ITEM
# ============================================================


class TreatmentPlanItemCreate(BaseModel):

    item_type: TreatmentPlanItemType

    reference_id: int | None = Field(
        default=None,
        gt=0,
    )

    item_name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    quantity: Decimal = Field(
        default=Decimal("1.00"),
        gt=0,
    )

    unit_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    notes: str | None = None


class TreatmentPlanItemUpdate(BaseModel):

    item_type: TreatmentPlanItemType | None = None

    reference_id: int | None = Field(
        default=None,
        gt=0,
    )

    item_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    quantity: Decimal | None = Field(
        default=None,
        gt=0,
    )

    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = None


class TreatmentPlanItemResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    item_type: str

    reference_id: int | None = None

    item_name: str

    description: str | None = None

    quantity: Decimal

    unit_price: Decimal

    total_price: Decimal

    notes: str | None = None


# ============================================================
# THERAPY
# ============================================================


class TreatmentPlanTherapyCreate(BaseModel):

    therapy_id: int | None = Field(
        default=None,
        gt=0,
    )

    therapy_name: str = Field(
        min_length=1,
        max_length=255,
    )

    sessions: int = Field(
        default=1,
        ge=1,
        le=10000,
    )

    frequency: str | None = Field(
        default=None,
        max_length=100,
    )

    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    unit_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    instructions: str | None = None

    notes: str | None = None


class TreatmentPlanTherapyUpdate(BaseModel):

    therapy_id: int | None = Field(
        default=None,
        gt=0,
    )

    therapy_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    sessions: int | None = Field(
        default=None,
        ge=1,
        le=10000,
    )

    frequency: str | None = Field(
        default=None,
        max_length=100,
    )

    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    instructions: str | None = None

    notes: str | None = None


class TreatmentPlanTherapyResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    therapy_id: int | None = None

    therapy_name: str

    sessions: int

    frequency: str | None = None

    duration_days: int | None = None

    unit_price: Decimal

    total_price: Decimal

    instructions: str | None = None

    notes: str | None = None


# ============================================================
# MEDICINE
# ============================================================


class TreatmentPlanMedicineCreate(BaseModel):

    medicine_id: int | None = Field(
        default=None,
        gt=0,
    )

    medicine_name: str = Field(
        min_length=1,
        max_length=255,
    )

    dosage: str | None = Field(
        default=None,
        max_length=100,
    )

    frequency: str | None = Field(
        default=None,
        max_length=100,
    )

    route: str | None = Field(
        default=None,
        max_length=100,
    )

    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    quantity: Decimal = Field(
        default=Decimal("1.00"),
        gt=0,
    )

    unit_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    instructions: str | None = None

    notes: str | None = None


class TreatmentPlanMedicineUpdate(BaseModel):

    medicine_id: int | None = Field(
        default=None,
        gt=0,
    )

    medicine_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    dosage: str | None = Field(
        default=None,
        max_length=100,
    )

    frequency: str | None = Field(
        default=None,
        max_length=100,
    )

    route: str | None = Field(
        default=None,
        max_length=100,
    )

    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )

    quantity: Decimal | None = Field(
        default=None,
        gt=0,
    )

    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    instructions: str | None = None

    notes: str | None = None


class TreatmentPlanMedicineResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    medicine_id: int | None = None

    medicine_name: str

    dosage: str | None = None

    frequency: str | None = None

    route: str | None = None

    duration_days: int | None = None

    quantity: Decimal

    unit_price: Decimal

    total_price: Decimal

    instructions: str | None = None

    notes: str | None = None


# ============================================================
# ROOM / STAY RECOMMENDATION
# ============================================================


class TreatmentPlanRoomUpdate(BaseModel):

    room_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    room_name: str | None = Field(
        default=None,
        max_length=150,
    )

    stay_duration_days: int = Field(
        ge=1,
        le=3650,
    )

    daily_rate: Decimal = Field(
        ge=0,
    )

    notes: str | None = None


class TreatmentPlanRoomResponse(BaseModel):

    room_type_id: int | None = None

    room_name: str | None = None

    stay_duration_days: int | None = None

    daily_rate: Decimal | None = None

    room_total: Decimal = Decimal("0.00")


# ============================================================
# SPECIALIST COLLABORATION
# ============================================================


class TreatmentPlanSpecialistCreate(BaseModel):

    specialist_id: int = Field(
        gt=0,
    )

    role: TreatmentPlanSpecialistRole = (
        "CONSULTING_SPECIALIST"
    )

    specialty: str | None = Field(
        default=None,
        max_length=150,
    )

    is_primary: bool = False

    notes: str | None = None


class TreatmentPlanSpecialistResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    specialist_id: int

    role: str

    specialty: str | None = None

    is_primary: bool

    status: str

    notes: str | None = None


# ============================================================
# PRICE CALCULATION RESPONSE
# ============================================================


class TreatmentPlanPricingResponse(BaseModel):

    treatment_plan_id: int

    therapy_total: Decimal = Decimal("0.00")

    medicine_total: Decimal = Decimal("0.00")

    room_total: Decimal = Decimal("0.00")

    service_total: Decimal = Decimal("0.00")

    subtotal: Decimal = Decimal("0.00")

    discount_amount: Decimal = Decimal("0.00")

    tax_amount: Decimal = Decimal("0.00")

    grand_total: Decimal = Decimal("0.00")


# ============================================================
# NESTED PRICING DETAIL
#
# Used inside:
# GET /treatment-plans/{id}
# ============================================================


class TreatmentPlanPricingDetail(BaseModel):

    therapy_total: Decimal = Decimal("0.00")

    medicine_total: Decimal = Decimal("0.00")

    room_total: Decimal = Decimal("0.00")

    service_total: Decimal = Decimal("0.00")

    subtotal: Decimal = Decimal("0.00")

    discount_amount: Decimal = Decimal("0.00")

    tax_amount: Decimal = Decimal("0.00")

    grand_total: Decimal = Decimal("0.00")


# ============================================================
# SUBMIT PLAN
# ============================================================


class TreatmentPlanSubmitRequest(BaseModel):

    submission_note: str | None = None


# ============================================================
# STATUS UPDATE
# ============================================================


class TreatmentPlanStatusUpdate(BaseModel):

    status: TreatmentPlanStatus

    reason: str | None = None

    notes: str | None = None


# ============================================================
# REQUEST MODIFICATION
# ============================================================


class TreatmentPlanModificationRequest(BaseModel):

    reason: str = Field(
        min_length=1,
    )

    comments: str | None = None


# ============================================================
# SUBMIT MODIFICATION
# ============================================================


class TreatmentPlanSubmitModificationRequest(BaseModel):

    modification_note: str | None = None


# ============================================================
# APPROVAL
# ============================================================


class TreatmentPlanApprovalRequest(BaseModel):

    approval_note: str | None = None


# ============================================================
# FINALIZATION
# ============================================================


class TreatmentPlanFinalizeRequest(BaseModel):

    finalization_note: str | None = None


# ============================================================
# CANCELLATION
# ============================================================


class TreatmentPlanCancelRequest(BaseModel):

    reason: str = Field(
        min_length=1,
    )

    notes: str | None = None


# ============================================================
# VERSION
# ============================================================


class TreatmentPlanVersionResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    version_number: int

    created_by: int

    status: str

    snapshot: dict[str, Any]

    change_note: str | None = None


# ============================================================
# STATUS HISTORY
# ============================================================


class TreatmentPlanStatusHistoryResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    treatment_plan_id: int

    from_status: str | None = None

    to_status: str

    changed_by: int

    reason: str | None = None

    notes: str | None = None


# ============================================================
# FULL DETAIL RESPONSE
#
# Used by:
#
# GET /api/v1/treatment-plans/{plan_id}
#
# This response contains:
#
# Basic plan
# Status
# Room
# Pricing
# Therapies
# Medicines
# Items
# Specialists
# Versions
# Status history
# ============================================================


class TreatmentPlanDetailResponse(
    TreatmentPlanResponse
):

    # --------------------------------------------------------
    # CHILD COLLECTIONS
    # --------------------------------------------------------

    therapies: list[
        TreatmentPlanTherapyResponse
    ] = Field(
        default_factory=list,
    )

    medicines: list[
        TreatmentPlanMedicineResponse
    ] = Field(
        default_factory=list,
    )

    items: list[
        TreatmentPlanItemResponse
    ] = Field(
        default_factory=list,
    )

    specialists: list[
        TreatmentPlanSpecialistResponse
    ] = Field(
        default_factory=list,
    )

    versions: list[
        TreatmentPlanVersionResponse
    ] = Field(
        default_factory=list,
    )

    status_history: list[
        TreatmentPlanStatusHistoryResponse
    ] = Field(
        default_factory=list,
    )

    # --------------------------------------------------------
    # NESTED ROOM
    # --------------------------------------------------------

    @computed_field(
        return_type=TreatmentPlanRoomResponse,
    )
    @property
    def room(
        self,
    ) -> TreatmentPlanRoomResponse:

        return TreatmentPlanRoomResponse(
            room_type_id=(
                self.room_type_id
            ),
            room_name=(
                self.room_name
            ),
            stay_duration_days=(
                self.stay_duration_days
            ),
            daily_rate=(
                self.room_daily_rate
            ),
            room_total=(
                self.room_total
                or Decimal("0.00")
            ),
        )

    # --------------------------------------------------------
    # NESTED PRICING
    # --------------------------------------------------------

    @computed_field(
        return_type=TreatmentPlanPricingDetail,
    )
    @property
    def pricing(
        self,
    ) -> TreatmentPlanPricingDetail:

        return TreatmentPlanPricingDetail(
            therapy_total=(
                self.therapy_total
                or Decimal("0.00")
            ),
            medicine_total=(
                self.medicine_total
                or Decimal("0.00")
            ),
            room_total=(
                self.room_total
                or Decimal("0.00")
            ),
            service_total=(
                self.service_total
                or Decimal("0.00")
            ),
            subtotal=(
                self.subtotal
                or Decimal("0.00")
            ),
            discount_amount=(
                self.discount_amount
                or Decimal("0.00")
            ),
            tax_amount=(
                self.tax_amount
                or Decimal("0.00")
            ),
            grand_total=(
                self.grand_total
                or Decimal("0.00")
            ),
        )