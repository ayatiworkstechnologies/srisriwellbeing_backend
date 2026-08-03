from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import (
    Patient,
    PatientDocument,
)
from app.modules.patients.portal.repository import (
    PatientPortalRepository,
)
from app.modules.patients.portal.schemas import (
    PatientDashboardData,
    PatientDashboardPatientData,
    PatientDashboardSummary,
    PatientProfileData,
    PatientProfileUpdate,
)
from app.modules.patients.portal.storage import (
    delete_stored_document,
    get_safe_document_path,
    save_patient_document,
)


class PatientPortalService:
    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        patient: Patient,
    ) -> PatientDashboardData:
        document_count = (
            await PatientPortalRepository
            .count_documents(
                db=db,
                patient_id=patient.id,
            )
        )

        full_name = " ".join(
            value
            for value in [
                patient.first_name,
                patient.middle_name,
                patient.last_name,
            ]
            if value
        ).strip()

        return PatientDashboardData(
            patient=(
                PatientDashboardPatientData(
                    id=patient.id,
                    patient_code=(
                        patient.patient_code
                    ),
                    first_name=(
                        patient.first_name
                    ),
                    middle_name=(
                        patient.middle_name
                    ),
                    last_name=(
                        patient.last_name
                    ),
                    full_name=full_name,
                    email=patient.email,
                    mobile_number=(
                        patient.mobile_number
                    ),
                    date_of_birth=(
                        patient.date_of_birth
                    ),
                    gender=patient.gender,
                    blood_group=(
                        patient.blood_group
                    ),
                    status=patient.status,
                    created_at=(
                        patient.created_at
                    ),
                )
            ),
            summary=(
                PatientDashboardSummary(
                    upcoming_appointments=0,
                    active_prescriptions=0,
                    new_reports=document_count,
                    pending_payments=0,
                )
            ),
        )

    @staticmethod
    def get_profile(
        patient: Patient,
    ) -> PatientProfileData:
        return (
            PatientProfileData
            .model_validate(patient)
        )

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        patient: Patient,
        payload: PatientProfileUpdate,
    ) -> PatientProfileData:
        update_data = (
            payload.model_dump(
                exclude_unset=True,
            )
        )

        for field_name, field_value in (
            update_data.items()
        ):
            setattr(
                patient,
                field_name,
                field_value,
            )

        normalized_name = " ".join(
            value
            for value in [
                patient.first_name,
                patient.middle_name,
                patient.last_name,
            ]
            if value
        )

        patient.normalized_full_name = (
            normalized_name
            .strip()
            .lower()
        )

        await PatientPortalRepository.save_patient(
            db=db,
            patient=patient,
        )

        await db.commit()
        await db.refresh(patient)

        return (
            PatientProfileData
            .model_validate(patient)
        )

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        patient: Patient,
    ) -> list[PatientDocument]:
        return (
            await PatientPortalRepository
            .list_documents(
                db=db,
                patient_id=patient.id,
            )
        )

    @staticmethod
    async def upload_document(
        db: AsyncSession,
        *,
        patient: Patient,
        user_id: int,
        upload_file: UploadFile,
        document_type: str,
        title: str,
    ) -> PatientDocument:
        stored_file = (
            await save_patient_document(
                upload_file=upload_file,
                patient_id=patient.id,
            )
        )

        try:
            document = (
                await PatientPortalRepository
                .create_document(
                    db=db,
                    patient_id=patient.id,
                    document_type=(
                        document_type
                    ),
                    title=title.strip(),
                    original_file_name=(
                        stored_file[
                            "original_file_name"
                        ]
                    ),
                    stored_file_name=(
                        stored_file[
                            "stored_file_name"
                        ]
                    ),
                    file_path=(
                        stored_file[
                            "file_path"
                        ]
                    ),
                    mime_type=(
                        stored_file[
                            "mime_type"
                        ]
                    ),
                    file_size=(
                        stored_file[
                            "file_size"
                        ]
                    ),
                    uploaded_by=user_id,
                )
            )

            await db.commit()
            await db.refresh(document)

            return document
        except Exception:
            await db.rollback()

            await delete_stored_document(
                stored_file.get(
                    "file_path"
                )
            )

            raise

    @staticmethod
    async def get_document(
        db: AsyncSession,
        patient: Patient,
        document_id: int,
    ) -> PatientDocument:
        document = (
            await PatientPortalRepository
            .get_document(
                db=db,
                patient_id=patient.id,
                document_id=document_id,
            )
        )

        if document is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Document not found",
            )

        return document

    @staticmethod
    async def get_document_file(
        db: AsyncSession,
        patient: Patient,
        document_id: int,
    ) -> tuple[
        PatientDocument,
        Path,
    ]:
        document = (
            await PatientPortalService
            .get_document(
                db=db,
                patient=patient,
                document_id=document_id,
            )
        )

        file_path = (
            get_safe_document_path(
                document.file_path
            )
        )

        return document, file_path

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        patient: Patient,
        document_id: int,
    ) -> PatientDocument:
        document = (
            await PatientPortalService
            .get_document(
                db=db,
                patient=patient,
                document_id=document_id,
            )
        )

        file_path = document.file_path

        await PatientPortalRepository.delete_document(
            db=db,
            document=document,
        )

        await db.commit()

        await delete_stored_document(
            file_path
        )

        return document