from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.password_service import PasswordService
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User, UserStatus
from app.modules.users.repository import UserRepository
from app.modules.users.schema import (
    UserCreateRequest,
    UserUpdateRequest,
)


class UserService:

    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        return await UserRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_user(
        db: AsyncSession,
        user_id: int,
    ) -> User:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    @staticmethod
    async def create_user(
        db: AsyncSession,
        payload: UserCreateRequest,
    ) -> User:
        normalized_email = payload.email.lower().strip()

        existing_user = await UserRepository.get_by_email(
            db=db,
            email=normalized_email,
        )

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        user = User(
            full_name=payload.full_name.strip(),
            email=normalized_email,
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

            if payload.role_ids:
                await RBACRepository.replace_user_roles(
                    db=db,
                    user_id=created_user.id,
                    role_ids=payload.role_ids,
                )

            await db.commit()
            await db.refresh(created_user)

            return created_user

        except IntegrityError as exc:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            ) from exc

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        payload: UserUpdateRequest,
    ) -> User:
        user = await UserService.get_user(
            db=db,
            user_id=user_id,
        )

        update_data = payload.model_dump(
            exclude_unset=True,
            exclude={"role_ids"},
        )

        if "email" in update_data:
            normalized_email = update_data["email"].lower().strip()

            existing_user = await UserRepository.get_by_email(
                db=db,
                email=normalized_email,
            )

            if (
                existing_user is not None
                and existing_user.id != user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

            update_data["email"] = normalized_email

        if "full_name" in update_data:
            update_data["full_name"] = (
                update_data["full_name"].strip()
            )

        for field_name, field_value in update_data.items():
            setattr(user, field_name, field_value)

        try:
            await UserRepository.save(
                db=db,
                user=user,
            )

            if payload.role_ids is not None:
                await RBACRepository.replace_user_roles(
                    db=db,
                    user_id=user.id,
                    role_ids=payload.role_ids,
                )

            await db.commit()
            await db.refresh(user)

            return user

        except IntegrityError as exc:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to update user",
            ) from exc

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        user = await UserService.get_user(
            db=db,
            user_id=user_id,
        )

        user.is_deleted = True
        user.is_active = False
        user.status = UserStatus.INACTIVE.value

        try:
            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "User deleted successfully",
        }

    @staticmethod
    async def activate_user(
        db: AsyncSession,
        user_id: int,
    ) -> User:
        user = await UserService.get_user(
            db=db,
            user_id=user_id,
        )

        user.is_active = True
        user.status = UserStatus.ACTIVE.value
        user.locked_until = None
        user.failed_login_attempts = 0

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user_id: int,
    ) -> User:
        user = await UserService.get_user(
            db=db,
            user_id=user_id,
        )

        user.is_active = False
        user.status = UserStatus.INACTIVE.value

        await db.commit()
        await db.refresh(user)

        return user