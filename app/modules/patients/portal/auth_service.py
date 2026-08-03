from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.password_service import PasswordService
from app.modules.patients.constants import PatientStatus
from app.modules.patients.models import Patient
from app.modules.patients.portal.schemas import (
    PatientRegisterRequest,
)
from app.modules.patients.service import PatientService
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User, UserStatus
from app.modules.users.repository import UserRepository


class PatientPortalAuthService:
    @staticmethod
    async def ensure_patient_profile(
        db: AsyncSession,
        user: User,
    ) -> Patient:
        linked_result = await db.execute(
            select(Patient).where(
                Patient.user_id == user.id
            )
        )
        linked_patient = linked_result.scalar_one_or_none()

        if linked_patient is not None:
            return linked_patient

        identity_filters = [
            Patient.email == user.email,
        ]

        if user.phone:
            identity_filters.append(
                Patient.mobile_number == user.phone
            )

        existing_result = await db.execute(
            select(Patient)
            .where(or_(*identity_filters))
            .order_by(Patient.id.asc())
            .limit(1)
        )
        existing_patient = existing_result.scalar_one_or_none()

        if existing_patient is not None:
            if (
                existing_patient.user_id is not None
                and existing_patient.user_id != user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "A patient profile with this email or phone "
                        "is linked to another account"
                    ),
                )

            existing_patient.user_id = user.id

            try:
                await db.commit()
                await db.refresh(existing_patient)
            except IntegrityError as exc:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unable to link the patient profile",
                ) from exc

            return existing_patient

        if not user.phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A phone number is required to create the patient "
                    "profile"
                ),
            )

        name_parts = user.full_name.strip().split(maxsplit=1)
        first_name = name_parts[0][:100]
        last_name = (
            name_parts[1][:100]
            if len(name_parts) > 1
            else None
        )
        patient = Patient(
            user_id=user.id,
            patient_code=(
                await PatientService.generate_patient_code(db=db)
            ),
            first_name=first_name,
            middle_name=None,
            last_name=last_name,
            normalized_full_name=user.full_name.strip().lower(),
            date_of_birth=None,
            gender=None,
            blood_group=None,
            mobile_number=user.phone,
            alternate_mobile_number=None,
            email=user.email,
            presenting_concern=None,
            status=PatientStatus.ACTIVE.value,
            is_duplicate_reviewed=False,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(patient)

        try:
            await db.flush()
            await db.commit()
            await db.refresh(patient)
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to create the patient profile",
            ) from exc

        return patient

    @staticmethod
    async def register(
        db: AsyncSession,
        payload: PatientRegisterRequest,
    ) -> dict:
        try:
            PasswordService.validate_password(
                payload.password
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=str(exc),
            ) from exc

        patient_role = await RBACRepository.get_role_by_name(
            db=db,
            name="patient",
        )

        if patient_role is None or not patient_role.is_active:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Patient registration is not configured",
            )

        existing_email = await UserRepository.get_by_email(
            db=db,
            email=payload.email,
        )

        if existing_email is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        existing_phone = await UserRepository.get_by_phone(
            db=db,
            phone=payload.phone,
        )

        if existing_phone is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A user with this phone number already exists"
                ),
            )

        existing_patient_result = await db.execute(
            select(Patient.id).where(
                Patient.mobile_number == payload.phone
            )
        )

        if existing_patient_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A patient with this phone number already exists"
                ),
            )

        patient_code = await PatientService.generate_patient_code(
            db=db,
        )
        normalized_name = payload.full_name.lower()

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            password_hash=PasswordService.hash_password(
                payload.password
            ),
            status=UserStatus.ACTIVE.value,
            is_active=True,
            is_verified=False,
        )

        try:
            created_user = await UserRepository.create(
                db=db,
                user=user,
            )

            await RBACRepository.replace_user_roles(
                db=db,
                user_id=created_user.id,
                role_ids=[patient_role.id],
            )

            patient = Patient(
                user_id=created_user.id,
                patient_code=patient_code,
                first_name=payload.full_name,
                middle_name=None,
                last_name=None,
                normalized_full_name=normalized_name,
                date_of_birth=None,
                gender=None,
                blood_group=None,
                mobile_number=payload.phone,
                alternate_mobile_number=None,
                email=payload.email,
                presenting_concern=None,
                status=PatientStatus.ACTIVE.value,
                is_duplicate_reviewed=False,
                created_by=created_user.id,
                updated_by=created_user.id,
            )
            db.add(patient)

            await db.flush()
            await db.commit()
            await db.refresh(created_user)
            await db.refresh(patient)

        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient account already exists",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Patient registered successfully",
            "data": {
                "patient": {
                    "id": patient.id,
                    "patient_code": patient.patient_code,
                    "full_name": payload.full_name,
                    "first_name": patient.first_name,
                    "middle_name": patient.middle_name,
                    "last_name": patient.last_name,
                    "email": patient.email,
                    "mobile_number": patient.mobile_number,
                    "status": patient.status,
                },
                "user": {
                    "id": created_user.id,
                    "full_name": created_user.full_name,
                    "email": created_user.email,
                    "phone": created_user.phone,
                },
                "role_id": patient_role.id,
                "roles": [patient_role.name],
            },
        }
