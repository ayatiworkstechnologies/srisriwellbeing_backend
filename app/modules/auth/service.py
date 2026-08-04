import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.auth.model import RefreshToken, UserSession
from app.modules.auth.password_reset_model import PasswordResetToken
from app.modules.auth.password_reset_repository import PasswordResetRepository
from app.modules.auth.password_service import PasswordService
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import RegisterRequest, UserProfileUpdateRequest
from app.modules.auth.token_service import TokenService
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User, UserStatus
from app.modules.users.repository import UserRepository


class AuthService:

    @staticmethod
    async def get_profile(
        current_user: User,
    ) -> dict:
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "data": {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "email": current_user.email,
                "phone": current_user.phone,
                "status": current_user.status,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "last_login_at": current_user.last_login_at,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at,
            },
        }

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        current_user: User,
        payload: UserProfileUpdateRequest,
    ) -> dict:
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        if "phone" in update_data:
            phone = update_data["phone"]

            if phone:
                existing_user = await UserRepository.get_by_phone(
                    db=db,
                    phone=phone,
                )

                if (
                    existing_user is not None
                    and existing_user.id != current_user.id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Phone number is already in use",
                    )

            current_user.phone = phone

        if "full_name" in update_data:
            current_user.full_name = update_data["full_name"]

        try:
            await UserRepository.save(
                db=db,
                user=current_user,
            )

            await db.commit()
            await db.refresh(current_user)

        except IntegrityError as exc:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile data is already in use",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": current_user.id,
                "full_name": current_user.full_name,
                "email": current_user.email,
                "phone": current_user.phone,
                "status": current_user.status,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "last_login_at": current_user.last_login_at,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at,
            },
        }

    @staticmethod
    async def activate_account(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_active and user.status == UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is already active",
            )

        user.is_active = True
        user.status = UserStatus.ACTIVE.value
        user.failed_login_attempts = 0
        user.locked_until = None

        try:
            await UserRepository.save(
                db=db,
                user=user,
            )

            await db.commit()
            await db.refresh(user)

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "User account activated successfully",
            "data": {
                "id": user.id,
                "email": user.email,
                "status": user.status,
                "is_active": user.is_active,
            },
        }

    @staticmethod
    async def deactivate_account(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is already inactive",
            )

        user.is_active = False
        user.status = UserStatus.INACTIVE.value

        try:
            await UserRepository.save(
                db=db,
                user=user,
            )

            revoked_sessions = await AuthRepository.revoke_all_user_sessions(
                db=db,
                user_id=user.id,
            )

            await db.commit()
            await db.refresh(user)

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "User account deactivated successfully",
            "data": {
                "id": user.id,
                "email": user.email,
                "status": user.status,
                "is_active": user.is_active,
                "revoked_sessions": revoked_sessions,
            },
        }

    # =========================================================
    # REGISTER
    # =========================================================

    @staticmethod
    async def register(
        db: AsyncSession,
        payload: RegisterRequest,
    ) -> dict:
        email = payload.email.lower().strip()
        phone = payload.phone.strip() if payload.phone else None

        role = await RBACRepository.get_role_by_id(
            db=db,
            role_id=payload.role_id,
        )

        if role is None or not role.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found or inactive",
            )

        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password and confirm password do not match",
            )

        try:
            PasswordService.validate_password(payload.password)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        existing_email = await UserRepository.get_by_email(
            db=db,
            email=email,
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        if phone:
            existing_phone = await UserRepository.get_by_phone(
                db=db,
                phone=phone,
            )

            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this phone number already exists",
                )

        user = User(
            full_name=payload.full_name.strip(),
            email=email,
            phone=phone,
            password_hash=PasswordService.hash_password(payload.password),
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
                role_ids=[role.id],
            )

            await db.commit()
            await db.refresh(created_user)

        except IntegrityError as exc:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "id": created_user.id,
                "full_name": created_user.full_name,
                "email": created_user.email,
                "phone": created_user.phone,
                "status": created_user.status,
                "is_active": created_user.is_active,
                "is_verified": created_user.is_verified,
                "role_id": role.id,
                "role": {
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.display_name,
                },
            },
        }

    # =========================================================
    # LOGIN
    # =========================================================

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        role_id: int | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
        allowed_roles: list[str] | None = None,
    ) -> dict:
        normalized_email = email.lower().strip()

        user = await UserRepository.get_by_email(
            db=db,
            email=normalized_email,
        )

        if user is None:
            await AuthRepository.record_login_attempt(
                db,
                email=normalized_email,
                was_successful=False,
                failure_reason="invalid_credentials",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        current_time = datetime.now()

        # Check temporary account lock.
        if (
            user.status == UserStatus.LOCKED.value
            and user.locked_until is not None
            and user.locked_until > current_time
        ):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked",
            )

        # Automatically unlock after lock duration expires.
        if user.status == UserStatus.LOCKED.value and (
            user.locked_until is None or user.locked_until <= current_time
        ):
            user.status = UserStatus.ACTIVE.value
            user.locked_until = None
            user.failed_login_attempts = 0

        password_is_valid = PasswordService.verify_password(
            plain_password=password,
            hashed_password=user.password_hash,
        )

        if not password_is_valid:
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.status = UserStatus.LOCKED.value
                user.locked_until = current_time + timedelta(
                    minutes=settings.ACCOUNT_LOCK_MINUTES
                )

            await AuthRepository.record_login_attempt(
                db,
                email=normalized_email,
                user_id=user.id,
                was_successful=False,
                failure_reason="invalid_credentials",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            try:
                await db.commit()

            except Exception:
                await db.rollback()
                raise

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if user.status == UserStatus.INACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if user.status == UserStatus.SUSPENDED.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is suspended",
            )

        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User account status is {user.status}",
            )

        # Load active roles assigned to this user.
        user_roles = await RBACRepository.get_user_roles(
            db=db,
            user_id=user.id,
        )

        normalized_allowed_roles = {
            role_name.strip().lower()
            for role_name in (allowed_roles or [])
            if role_name and role_name.strip()
        }

        selected_role = next(
            (
                role
                for role in user_roles
                if role.is_active
                and (role_id is None or role.id == role_id)
                and (
                    not normalized_allowed_roles
                    or role.name.strip().lower() in normalized_allowed_roles
                )
            ),
            None,
        )

        if selected_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Selected role is not assigned to this user",
            )

        roles = [selected_role.name]

        # Scope this session to the selected role only.
        permissions = list(
            dict.fromkeys(
                permission.code
                for permission in selected_role.permissions
                if permission.is_active
            )
        )

        temporary_token_hash = secrets.token_hex(32)

        session = UserSession(
            user_id=user.id,
            refresh_token_hash=temporary_token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=(
                current_time
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            ),
            is_active=True,
        )

        try:
            created_session = await AuthRepository.create_session(
                db=db,
                session=session,
            )

            access_token = TokenService.create_access_token(
                user_id=user.id,
                email=user.email,
                session_id=created_session.id,
                role_id=selected_role.id,
                roles=roles,
                permissions=permissions,
            )

            refresh_token = TokenService.create_refresh_token(
                user_id=user.id,
                session_id=created_session.id,
                role_id=selected_role.id,
            )

            created_session.refresh_token_hash = TokenService.hash_token(
                refresh_token
            )

            await AuthRepository.create_refresh_token(
                db,
                RefreshToken(
                    user_id=user.id,
                    session_id=created_session.id,
                    token_hash=created_session.refresh_token_hash,
                    expires_at=created_session.expires_at,
                ),
            )

            await AuthRepository.record_login_attempt(
                db,
                email=normalized_email,
                user_id=user.id,
                was_successful=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            user.failed_login_attempts = 0
            user.locked_until = None
            user.status = UserStatus.ACTIVE.value
            user.last_login_at = current_time

            await db.commit()

        except IntegrityError as exc:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to create login session",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "status": user.status,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "last_login_at": user.last_login_at,
                },
                "roles": roles,
                "role_id": selected_role.id,
                "role": {
                    "id": selected_role.id,
                    "name": selected_role.name,
                    "display_name": selected_role.display_name,
                },
                "permissions": permissions,
            },
        }

    # =========================================================
    # REFRESH TOKEN
    # =========================================================

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> dict:
        try:
            payload = TokenService.decode_token(refresh_token)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        token_type = payload.get("token_type")
        user_id_value = payload.get("sub")
        session_id_value = payload.get("session_id")
        role_id_value = payload.get("role_id")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        if (
            user_id_value is None
            or session_id_value is None
            or role_id_value is None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        try:
            user_id = int(user_id_value)
            session_id = int(session_id_value)
            role_id = int(role_id_value)

        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            ) from exc

        session = await AuthRepository.get_active_session(
            db=db,
            session_id=session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is expired or revoked",
            )

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token does not match session",
            )

        token_is_valid = TokenService.verify_token_hash(
            token=refresh_token,
            stored_hash=session.refresh_token_hash,
        )

        if not token_is_valid:
            await AuthRepository.revoke_session(
                db=db,
                session=session,
            )

            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or already used",
            )

        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found",
            )

        user_roles = await RBACRepository.get_user_roles(
            db=db,
            user_id=user.id,
        )

        selected_role = next(
            (
                role
                for role in user_roles
                if role.id == role_id and role.is_active
            ),
            None,
        )

        if selected_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session role is no longer assigned to this user",
            )

        roles = [selected_role.name]

        permissions = list(
            dict.fromkeys(
                permission.code
                for permission in selected_role.permissions
                if permission.is_active
            )
        )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User account status is {user.status}",
            )

        new_access_token = TokenService.create_access_token(
            user_id=user.id,
            email=user.email,
            session_id=session.id,
            role_id=selected_role.id,
            roles=roles,
            permissions=permissions,
        )

        new_refresh_token = TokenService.create_refresh_token(
            user_id=user.id,
            session_id=session.id,
            role_id=selected_role.id,
        )

        new_refresh_token_hash = TokenService.hash_token(new_refresh_token)

        new_expiry = datetime.now() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        try:
            await AuthRepository.update_refresh_token_hash(
                db=db,
                session=session,
                refresh_token_hash=new_refresh_token_hash,
                expires_at=new_expiry,
            )

            await AuthRepository.rotate_refresh_token(
                db,
                old_hash=TokenService.hash_token(refresh_token),
                replacement=RefreshToken(
                    user_id=user.id,
                    session_id=session.id,
                    token_hash=new_refresh_token_hash,
                    expires_at=new_expiry,
                ),
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
                "role_id": selected_role.id,
            },
        }

    # =========================================================
    # LOGOUT
    # =========================================================

    @staticmethod
    async def logout(
        db: AsyncSession,
        session_id: int,
    ) -> dict:
        session = await AuthRepository.get_session_by_id(
            db=db,
            session_id=session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        if not session.is_active or session.revoked_at is not None:
            return {
                "success": True,
                "message": "Session already logged out",
            }

        try:
            await AuthRepository.revoke_session(
                db=db,
                session=session,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Logout successful",
        }

    # =========================================================
    # LOGOUT ALL
    # =========================================================

    @staticmethod
    async def logout_all(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        try:
            revoked_count = await AuthRepository.revoke_all_user_sessions(
                db=db,
                user_id=user_id,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Logged out from all devices successfully",
            "data": {
                "revoked_sessions": revoked_count,
            },
        }

    # =========================================================
    # GET USER SESSIONS
    # =========================================================

    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        user_id: int,
        current_session_id: int,
    ) -> dict:
        sessions = await AuthRepository.get_user_sessions(
            db=db,
            user_id=user_id,
        )

        session_data = []

        for session in sessions:
            session_data.append(
                {
                    "id": session.id,
                    "user_agent": session.user_agent,
                    "ip_address": session.ip_address,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                    "revoked_at": session.revoked_at,
                    "is_active": session.is_active,
                    "is_current": (session.id == current_session_id),
                }
            )

        return {
            "success": True,
            "message": "Sessions retrieved successfully",
            "data": session_data,
        }

    # =========================================================
    # REVOKE SPECIFIC USER SESSION
    # =========================================================

    @staticmethod
    async def revoke_user_session(
        db: AsyncSession,
        user_id: int,
        session_id: int,
        current_session_id: int,
    ) -> dict:
        session = await AuthRepository.get_session_by_id(
            db=db,
            session_id=session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot revoke another user's session",
            )

        if session.id == current_session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /auth/logout to revoke the current session",
            )

        if not session.is_active or session.revoked_at is not None:
            return {
                "success": True,
                "message": "Session is already revoked",
            }

        try:
            await AuthRepository.revoke_session(
                db=db,
                session=session,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Session revoked successfully",
            "data": {
                "session_id": session.id,
            },
        }

    # =========================================================
    # CHANGE PASSWORD
    # =========================================================

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> dict:
        current_password_is_valid = PasswordService.verify_password(
            plain_password=current_password,
            hashed_password=user.password_hash,
        )

        if not current_password_is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        current_and_new_are_same = PasswordService.verify_password(
            plain_password=new_password,
            hashed_password=user.password_hash,
        )

        if current_and_new_are_same:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "New password must be different " "from current password"
                ),
            )

        try:
            PasswordService.validate_password(new_password)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        new_password_hash = PasswordService.hash_password(new_password)

        try:
            await UserRepository.update_password(
                db=db,
                user=user,
                password_hash=new_password_hash,
            )

            revoked_sessions = await AuthRepository.revoke_all_user_sessions(
                db=db,
                user_id=user.id,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": (
                "Password changed successfully. " "Please log in again."
            ),
            "data": {
                "revoked_sessions": revoked_sessions,
            },
        }

    # =========================================================
    # FORGOT PASSWORD
    # =========================================================

    @staticmethod
    async def forgot_password(
        db: AsyncSession,
        email: str,
    ) -> dict:
        normalized_email = email.lower().strip()

        generic_response = {
            "success": True,
            "message": (
                "If an account exists for this email, "
                "password reset instructions have been generated."
            ),
        }

        user = await UserRepository.get_by_email(
            db=db,
            email=normalized_email,
        )

        # Always return the same response to prevent email enumeration.
        if user is None:
            return generic_response

        if not user.is_active:
            return generic_response

        plain_reset_token = TokenService.create_password_reset_token()

        reset_token_hash = TokenService.hash_password_reset_token(
            plain_reset_token
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=reset_token_hash,
            expires_at=(datetime.now() + timedelta(minutes=30)),
            is_used=False,
        )

        try:
            # Invalidate any older unused reset tokens.
            await PasswordResetRepository.invalidate_user_tokens(
                db=db,
                user_id=user.id,
            )

            await PasswordResetRepository.create(
                db=db,
                reset_token=reset_token,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": (
                "If an account exists for this email, "
                "password reset instructions have been generated."
            ),
            # Only for local development/testing.
            # Remove this after email integration is completed.
            "development_data": {
                "reset_token": plain_reset_token,
                "expires_in_minutes": 30,
            },
        }

    # =========================================================
    # RESET PASSWORD
    # =========================================================

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> dict:
        cleaned_token = token.strip()

        if not cleaned_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token is required",
            )

        try:
            PasswordService.validate_password(new_password)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        reset_token_hash = TokenService.hash_password_reset_token(
            cleaned_token
        )

        reset_token = await PasswordResetRepository.get_valid_by_hash(
            db=db,
            token_hash=reset_token_hash,
        )

        if reset_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Reset token is invalid, expired, " "or already used"),
            )

        user = await UserRepository.get_by_id(
            db=db,
            user_id=reset_token.user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        same_as_current_password = PasswordService.verify_password(
            plain_password=new_password,
            hashed_password=user.password_hash,
        )

        if same_as_current_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "New password must be different "
                    "from the current password"
                ),
            )

        new_password_hash = PasswordService.hash_password(new_password)

        try:
            await UserRepository.update_password(
                db=db,
                user=user,
                password_hash=new_password_hash,
            )

            await PasswordResetRepository.mark_as_used(
                db=db,
                reset_token=reset_token,
            )

            revoked_sessions = await AuthRepository.revoke_all_user_sessions(
                db=db,
                user_id=user.id,
            )

            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": (
                "Password reset successfully. " "Please log in again."
            ),
            "data": {
                "revoked_sessions": revoked_sessions,
            },
        }
