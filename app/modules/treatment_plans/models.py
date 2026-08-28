from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


# ============================================================
# TREATMENT PLAN
# ============================================================


class TreatmentPlan(BaseModel):
    __tablename__ = "treatment_plans"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    consultation_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    referral_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "specialist_referrals.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    plan_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    clinical_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    stay_duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Do not add a ForeignKey until room master table exists.
    room_type_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    room_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    room_daily_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    therapy_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    medicine_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    room_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    service_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="DRAFT",
        index=True,
    )

    current_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
     DateTime,
    nullable=True,
    )

    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships

    versions: Mapped[list["TreatmentPlanVersion"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    items: Mapped[list["TreatmentPlanItem"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    therapies: Mapped[list["TreatmentPlanTherapy"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    medicines: Mapped[list["TreatmentPlanMedicine"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    specialists: Mapped[list["TreatmentPlanSpecialist"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    status_history: Mapped[list["TreatmentPlanStatusHistory"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_treatment_plans_patient_status",
            "patient_id",
            "status",
        ),
        Index(
            "ix_treatment_plans_created_by_status",
            "created_by",
            "status",
        ),
    )


# ============================================================
# TREATMENT PLAN VERSION
# ============================================================


class TreatmentPlanVersion(BaseModel):
    __tablename__ = "treatment_plan_versions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    # Full immutable plan snapshot.
    snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    change_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="versions",
    )

    __table_args__ = (
        Index(
            "uq_treatment_plan_version",
            "treatment_plan_id",
            "version_number",
            unique=True,
        ),
    )


# ============================================================
# TREATMENT PLAN ITEM
# ============================================================


class TreatmentPlanItem(BaseModel):
    __tablename__ = "treatment_plan_items"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Optional ID from service/therapy/procedure master.
    reference_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    item_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=1,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="items",
    )


# ============================================================
# TREATMENT PLAN THERAPY
# ============================================================


class TreatmentPlanTherapy(BaseModel):
    __tablename__ = "treatment_plan_therapies"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Add FK when therapy master table exists.
    therapy_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    therapy_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sessions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    frequency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="therapies",
    )


# ============================================================
# TREATMENT PLAN MEDICINE
# ============================================================


class TreatmentPlanMedicine(BaseModel):
    __tablename__ = "treatment_plan_medicines"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Add FK when medicine master table exists.
    medicine_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    medicine_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    dosage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    frequency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    route: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=1,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="medicines",
    )


# ============================================================
# TREATMENT PLAN SPECIALIST
# ============================================================


class TreatmentPlanSpecialist(BaseModel):
    __tablename__ = "treatment_plan_specialists"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    specialist_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="CONSULTING_SPECIALIST",
    )

    specialty: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="specialists",
    )

    __table_args__ = (
        Index(
            "uq_treatment_plan_specialist",
            "treatment_plan_id",
            "specialist_id",
            unique=True,
        ),
    )


# ============================================================
# TREATMENT PLAN STATUS HISTORY
# ============================================================


class TreatmentPlanStatusHistory(BaseModel):
    __tablename__ = "treatment_plan_status_history"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    treatment_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "treatment_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    from_status: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    to_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    treatment_plan: Mapped["TreatmentPlan"] = relationship(
        back_populates="status_history",
    )