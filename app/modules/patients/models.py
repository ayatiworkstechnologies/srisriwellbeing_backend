from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.modules.patients.constants import (
    AddressType,
    DocumentType,
    DuplicateMatchStatus,
    Gender,
    IdentifierType,
    PatientStatus,
)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    patient_code: Mapped[str] = mapped_column(
    String(10),
    nullable=False,
    unique=True,
    index=True,
)

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    middle_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    normalized_full_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )

    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    gender: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )

    mobile_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    alternate_mobile_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    presenting_concern: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PatientStatus.ACTIVE.value,
        index=True,
    )

    is_duplicate_reviewed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    addresses: Mapped[list["PatientAddress"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    identifiers: Mapped[list["PatientIdentifier"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    documents: Mapped[list["PatientDocument"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_patients_mobile_dob",
            "mobile_number",
            "date_of_birth",
        ),
        Index(
            "ix_patients_name_dob",
            "normalized_full_name",
            "date_of_birth",
        ),
    )


class PatientAddress(Base):
    __tablename__ = "patient_addresses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    address_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=AddressType.HOME.value,
    )

    address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address_line_2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    landmark: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="India",
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="addresses"
    )


class PatientIdentifier(Base):
    __tablename__ = "patient_identifiers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    identifier_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    issuing_country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="identifiers"
    )

    __table_args__ = (
        UniqueConstraint(
            "identifier_type",
            "identifier_value",
            name="uq_patient_identifier_type_value",
        ),
    )


class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DocumentType.OTHER.value,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    uploaded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="documents"
    )


class PatientDuplicateMatch(Base):
    __tablename__ = "patient_duplicate_matches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source_patient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    matched_patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mobile_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    email_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    date_of_birth_match: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    name_similarity_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    overall_match_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DuplicateMatchStatus.PENDING_REVIEW.value,
    )

    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )