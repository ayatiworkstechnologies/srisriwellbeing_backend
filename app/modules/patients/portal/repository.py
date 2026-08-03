from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.patients.models import (
    Patient,
    PatientDocument,
)


class PatientPortalRepository:
    @staticmethod
    async def get_patient_by_user_id(
        db: AsyncSession,
        user_id: int,
    ) -> Patient | None:
        statement = (
            select(Patient)
            .options(
                selectinload(
                    Patient.addresses
                ),
                selectinload(
                    Patient.identifiers
                ),
                selectinload(
                    Patient.documents
                ),
            )
            .where(
                Patient.user_id == user_id
            )
        )

        result = await db.execute(
            statement
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def save_patient(
        db: AsyncSession,
        patient: Patient,
    ) -> Patient:
        await db.flush()
        await db.refresh(patient)

        return patient

    @staticmethod
    async def count_documents(
        db: AsyncSession,
        patient_id: int,
    ) -> int:
        statement = (
            select(
                func.count(
                    PatientDocument.id
                )
            )
            .where(
                PatientDocument.patient_id
                == patient_id
            )
        )

        result = await db.execute(
            statement
        )

        return int(
            result.scalar_one() or 0
        )

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        patient_id: int,
    ) -> list[PatientDocument]:
        statement = (
            select(PatientDocument)
            .where(
                PatientDocument.patient_id
                == patient_id
            )
            .order_by(
                PatientDocument.created_at.desc(),
                PatientDocument.id.desc(),
            )
        )

        result = await db.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def get_document(
        db: AsyncSession,
        patient_id: int,
        document_id: int,
    ) -> PatientDocument | None:
        statement = (
            select(PatientDocument)
            .where(
                PatientDocument.id
                == document_id,
                PatientDocument.patient_id
                == patient_id,
            )
        )

        result = await db.execute(
            statement
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(
        db: AsyncSession,
        *,
        patient_id: int,
        document_type: str,
        title: str,
        original_file_name: str,
        stored_file_name: str,
        file_path: str,
        mime_type: str,
        file_size: int,
        uploaded_by: int,
    ) -> PatientDocument:
        document = PatientDocument(
            patient_id=patient_id,
            document_type=document_type,
            title=title,
            original_file_name=(
                original_file_name
            ),
            stored_file_name=(
                stored_file_name
            ),
            file_path=file_path,
            file_url=None,
            mime_type=mime_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
        )

        db.add(document)

        await db.flush()
        await db.refresh(document)

        return document

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document: PatientDocument,
    ) -> None:
        await db.delete(document)
        await db.flush()