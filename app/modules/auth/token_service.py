import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


class TokenService:
    @staticmethod
    def create_access_token(
        user_id: int,
        email: str,
        session_id: int,
        role_id: int | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),
            "email": email,
            "session_id": session_id,
            "token_type": "access",
            "role_id": role_id,
            "roles": roles or [],
            "permissions": permissions or [],
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def create_refresh_token(
        user_id: int,
        session_id: int,
        role_id: int | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "session_id": session_id,
            "token_type": "refresh",
            "role_id": role_id,
            "jti": secrets.token_urlsafe(32),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )

        except JWTError as exc:
            raise ValueError("Token is invalid or expired") from exc

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_token_hash(
        token: str,
        stored_hash: str,
    ) -> bool:
        incoming_hash = TokenService.hash_token(token)

        return secrets.compare_digest(
            incoming_hash,
            stored_hash,
        )

    @staticmethod
    def create_password_reset_token() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_password_reset_token(
        token: str,
    ) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
