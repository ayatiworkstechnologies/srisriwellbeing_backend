from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.patients.models import (
    Patient,
    PatientAddress,
    PatientIdentifier,
)


class PatientRepository:
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        patient_id: int,
    ) -> Optional[Patient]:
        statement = (
            select(Patient)
            .options(
                selectinload(Patient.addresses),
                selectinload(Patient.identifiers),
                selectinload(Patient.documents),
            )
            .where(Patient.id == patient_id)
        )

        result = await db.execute(statement)

        return result.scalars().unique().one_or_none()

    @staticmethod
    async def get_by_code(
        db: AsyncSession,
        patient_code: str,
    ) -> Optional[Patient]:
        statement = (
            select(Patient)
            .options(
                selectinload(Patient.addresses),
                selectinload(Patient.identifiers),
                selectinload(Patient.documents),
            )
            .where(Patient.patient_code == patient_code)
        )

        result = await db.execute(statement)

        return result.scalars().unique().one_or_none()

    @staticmethod
    async def list_patients(
        db: AsyncSession,
        *,
        search: Optional[str],
        status: Optional[str],
        skip: int,
        limit: int,
    ) -> tuple[list[Patient], int]:
        filters = []

        if search:
            keyword = f"%{search.strip().lower()}%"

            filters.append(
                or_(
                    func.lower(Patient.patient_code).like(keyword),
                    func.lower(Patient.normalized_full_name).like(keyword),
                    func.lower(Patient.mobile_number).like(keyword),
                    func.lower(Patient.email).like(keyword),
                )
            )

        if status:
            filters.append(Patient.status == status)

        count_statement = select(
            func.count(Patient.id)
        )

        list_statement = (
            select(Patient)
            .order_by(Patient.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        if filters:
            count_statement = count_statement.where(*filters)
            list_statement = list_statement.where(*filters)

        total = int(
            await db.scalar(count_statement) or 0
        )

        result = await db.execute(list_statement)

        return result.scalars().unique().all(), total

    @staticmethod
    async def create(
        db: AsyncSession,
        patient: Patient,
    ) -> Patient:
        db.add(patient)
        await db.flush()
        await db.refresh(patient)

        return patient

    @staticmethod
    async def create_address(
        db: AsyncSession,
        address: PatientAddress,
    ) -> PatientAddress:
        db.add(address)
        await db.flush()
        await db.refresh(address)

        return address

    @staticmethod
    async def create_identifier(
        db: AsyncSession,
        identifier: PatientIdentifier,
    ) -> PatientIdentifier:
        db.add(identifier)
        await db.flush()
        await db.refresh(identifier)

        return identifier