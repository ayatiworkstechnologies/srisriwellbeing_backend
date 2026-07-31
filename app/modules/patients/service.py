import logging
from datetime import datetime
from random import randint
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.patients.constants import PatientStatus
from app.modules.patients.models import Patient
from app.modules.patients.schemas import (
    PatientCreate,
    PatientDuplicateCheckRequest,
    PatientUpdate,
)


logger = logging.getLogger(__name__)


class PatientService:
    # ------------------------------------------------------------------
    # Relationship loading
    # ------------------------------------------------------------------

    @staticmethod
    def _patient_relationship_options() -> list:
        """
        Load Patient relationships only when they exist in the model.

        This helps prevent async SQLAlchemy lazy-loading errors when
        FastAPI converts the Patient model into a response schema.
        """

        options = []

        for relationship_name in (
            "addresses",
            "identifiers",
            "documents",
        ):
            if hasattr(Patient, relationship_name):
                options.append(
                    selectinload(
                        getattr(Patient, relationship_name)
                    )
                )

        return options

    # ------------------------------------------------------------------
    # Normalise patient name
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_full_name(
        first_name: Optional[str],
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> str:
        name_parts = [
            first_name,
            middle_name,
            last_name,
        ]

        full_name = " ".join(
            str(part).strip()
            for part in name_parts
            if part and str(part).strip()
        )

        return " ".join(
            full_name.lower().split()
        )

    # ------------------------------------------------------------------
    # Generate patient code
    # ------------------------------------------------------------------

    @staticmethod
    async def generate_patient_code(
        db: AsyncSession,
    ) -> str:
        for _ in range(20):
            patient_code = (
                f"PT{datetime.now().strftime('%Y%m%d')}"
                f"{randint(1000, 9999)}"
            )

            result = await db.execute(
                select(Patient.id).where(
                    Patient.patient_code == patient_code
                )
            )

            if result.scalar_one_or_none() is None:
                return patient_code

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate a unique patient code",
        )

    # ------------------------------------------------------------------
    # 1. Create patient
    # ------------------------------------------------------------------

    @staticmethod
    async def create_patient(
        db: AsyncSession,
        payload: PatientCreate,
        created_by: int,
    ) -> Patient:
        mobile_number = payload.mobile_number.strip()
        first_name = payload.first_name.strip()

        existing_result = await db.execute(
            select(Patient).where(
                Patient.mobile_number == mobile_number
            )
        )

        existing_patient = (
            existing_result.scalars().first()
        )

        if existing_patient is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A patient with this mobile number "
                    "already exists"
                ),
            )

        patient_code = (
            await PatientService.generate_patient_code(
                db=db
            )
        )

        normalized_full_name = (
            PatientService.normalize_full_name(
                first_name=first_name,
            )
        )

        patient = Patient(
            patient_code=patient_code,
            first_name=first_name,
            middle_name=None,
            last_name=None,
            normalized_full_name=normalized_full_name,
            date_of_birth=None,
            gender=None,
            mobile_number=mobile_number,
            alternate_mobile_number=None,
            email=None,
            presenting_concern=None,
            status=PatientStatus.ACTIVE,
            is_duplicate_reviewed=False,
            created_by=created_by,
            updated_by=created_by,
        )

        db.add(patient)

        try:
            await db.flush()
            patient_id = patient.id

            await db.commit()

            return await PatientService.get_patient(
                db=db,
                patient_id=patient_id,
            )

        except HTTPException:
            await db.rollback()
            raise

        except IntegrityError as exc:
            await db.rollback()

            logger.exception(
                "Patient creation integrity error: %s",
                exc.orig,
            )

            error_message = str(exc.orig).lower()

            if "mobile" in error_message:
                detail = (
                    "A patient with this mobile number "
                    "already exists"
                )
            elif "patient_code" in error_message:
                detail = (
                    "Patient code already exists. "
                    "Please try again"
                )
            else:
                detail = (
                    "Patient could not be created due to "
                    "a database constraint"
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            ) from exc

        except Exception as exc:
            await db.rollback()

            logger.exception(
                "Unexpected patient creation error: %s",
                exc,
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Unexpected error while creating patient"
                ),
            ) from exc

    # ------------------------------------------------------------------
    # 2. List patients
    # ------------------------------------------------------------------

    @staticmethod
    async def list_patients(
        db: AsyncSession,
        search: Optional[str] = None,
        patient_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        filters = []

        if search:
            search_value = search.strip()

            if search_value:
                search_pattern = f"%{search_value}%"

                filters.append(
                    or_(
                        Patient.patient_code.ilike(
                            search_pattern
                        ),
                        Patient.first_name.ilike(
                            search_pattern
                        ),
                        Patient.normalized_full_name.ilike(
                            search_pattern
                        ),
                        Patient.mobile_number.ilike(
                            search_pattern
                        ),
                        Patient.email.ilike(
                            search_pattern
                        ),
                    )
                )

        if patient_status:
            filters.append(
                Patient.status == patient_status
            )

        count_query = select(
            func.count(Patient.id)
        )

        patient_query = (
            select(Patient)
            .options(
                *PatientService
                ._patient_relationship_options()
            )
            .order_by(
                Patient.created_at.desc(),
                Patient.id.desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        if filters:
            count_query = count_query.where(*filters)
            patient_query = patient_query.where(*filters)

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        patient_result = await db.execute(
            patient_query
        )

        patients = (
            patient_result
            .scalars()
            .unique()
            .all()
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": patients,
        }

    # ------------------------------------------------------------------
    # 3. Get patient
    # ------------------------------------------------------------------

    @staticmethod
    async def get_patient(
        db: AsyncSession,
        patient_id: int,
    ) -> Patient:
        result = await db.execute(
            select(Patient)
            .options(
                *PatientService
                ._patient_relationship_options()
            )
            .where(
                Patient.id == patient_id
            )
        )

        patient = (
            result
            .scalars()
            .unique()
            .first()
        )

        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        return patient

    # ------------------------------------------------------------------
    # 4. Update patient
    # ------------------------------------------------------------------

    @staticmethod
    async def update_patient(
        db: AsyncSession,
        patient_id: int,
        payload: PatientUpdate,
        updated_by: int,
    ) -> Patient:
        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id
            )
        )

        patient = result.scalars().first()

        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields were provided for update",
            )

        if "mobile_number" in update_data:
            mobile_number = update_data[
                "mobile_number"
            ]

            if mobile_number is not None:
                mobile_number = mobile_number.strip()

                duplicate_result = await db.execute(
                    select(Patient.id).where(
                        Patient.mobile_number
                        == mobile_number,
                        Patient.id != patient_id,
                    )
                )

                duplicate_id = (
                    duplicate_result.scalar_one_or_none()
                )

                if duplicate_id is not None:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_409_CONFLICT
                        ),
                        detail=(
                            "Another patient already uses "
                            "this mobile number"
                        ),
                    )

                update_data[
                    "mobile_number"
                ] = mobile_number

        for field_name in (
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "presenting_concern",
            "alternate_mobile_number",
        ):
            if field_name in update_data:
                value = update_data[field_name]

                if isinstance(value, str):
                    cleaned_value = value.strip()

                    update_data[field_name] = (
                        cleaned_value
                        if cleaned_value
                        else None
                    )

        for field_name, value in update_data.items():
            if hasattr(patient, field_name):
                setattr(
                    patient,
                    field_name,
                    value,
                )

        patient.normalized_full_name = (
            PatientService.normalize_full_name(
                first_name=patient.first_name,
                middle_name=patient.middle_name,
                last_name=patient.last_name,
            )
        )

        patient.updated_by = updated_by

        try:
            await db.flush()
            await db.commit()

            return await PatientService.get_patient(
                db=db,
                patient_id=patient_id,
            )

        except HTTPException:
            await db.rollback()
            raise

        except IntegrityError as exc:
            await db.rollback()

            logger.exception(
                "Patient update integrity error: %s",
                exc.orig,
            )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Patient could not be updated because "
                    "the submitted data already exists"
                ),
            ) from exc

        except Exception as exc:
            await db.rollback()

            logger.exception(
                "Unexpected patient update error: %s",
                exc,
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Unexpected error while updating patient"
                ),
            ) from exc

    # ------------------------------------------------------------------
    # 5. Duplicate check
    # ------------------------------------------------------------------

    @staticmethod
    async def check_duplicates(
        db: AsyncSession,
        payload: PatientDuplicateCheckRequest,
    ) -> dict:
        mobile_number = (
            payload.mobile_number.strip()
        )

        result = await db.execute(
            select(Patient).where(
                Patient.mobile_number == mobile_number
            )
        )

        patient = result.scalars().first()

        if patient is None:
            return {
                "is_duplicate": False,
                "patient_id": None,
                "patient_code": None,
                "message": (
                    "No patient found with this "
                    "mobile number"
                ),
            }

        return {
            "is_duplicate": True,
            "patient_id": patient.id,
            "patient_code": patient.patient_code,
            "message": (
                "A patient with this mobile number "
                "already exists"
            ),
        }
    # ------------------------------------------------------------------
    # 6. Delete patient
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_patient(
        db: AsyncSession,
        patient_id: int,
    ) -> dict:
        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id
            )
        )

        patient = result.scalars().first()

        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

        try:
            await db.delete(patient)
            await db.commit()

            return {
                "message": "Patient deleted successfully",
                "patient_id": patient_id,
            }

        except IntegrityError as exc:
            await db.rollback()

            logger.exception(
                "Patient deletion integrity error: %s",
                exc.orig,
            )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Patient cannot be deleted because related "
                    "records still exist"
                ),
            ) from exc

        except Exception as exc:
            await db.rollback()

            logger.exception(
                "Unexpected patient deletion error: %s",
                exc,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error while deleting patient",
            ) from exc