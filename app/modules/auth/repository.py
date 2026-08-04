from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import LoginAttempt, RefreshToken, UserSession


class AuthRepository:
    @staticmethod
    async def record_login_attempt(
        db: AsyncSession,
        *,
        email: str,
        was_successful: bool,
        user_id: int | None = None,
        failure_reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        db.add(
            LoginAttempt(
                user_id=user_id,
                email=email,
                was_successful=was_successful,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await db.flush()

    @staticmethod
    async def create_refresh_token(
        db: AsyncSession,
        token: RefreshToken,
    ) -> None:
        db.add(token)
        await db.flush()

    @staticmethod
    async def rotate_refresh_token(
        db: AsyncSession,
        *,
        old_hash: str,
        replacement: RefreshToken,
    ) -> None:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == old_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )
        db.add(replacement)
        await db.flush()

    @staticmethod
    async def create_session(
        db: AsyncSession,
        session: UserSession,
    ) -> UserSession:
        db.add(session)

        await db.flush()
        await db.refresh(session)

        return session

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: int,
    ) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.id == session_id,
        )

        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_session(
        db: AsyncSession,
        session_id: int,
    ) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.is_active.is_(True),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.utcnow(),
        )

        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_refresh_token_hash(
        db: AsyncSession,
        session: UserSession,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> UserSession:
        session.refresh_token_hash = refresh_token_hash
        session.expires_at = expires_at

        await db.flush()
        await db.refresh(session)

        return session

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        session: UserSession,
    ) -> None:
        session.is_active = False
        session.revoked_at = datetime.utcnow()

        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == session.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )

        await db.flush()

    @staticmethod
    async def revoke_all_user_sessions(
        db: AsyncSession,
        user_id: int,
    ) -> int:
        statement = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active.is_(True),
            )
            .values(
                is_active=False,
                revoked_at=datetime.utcnow(),
            )
        )

        result = await db.execute(statement)

        session_ids = select(UserSession.id).where(
            UserSession.user_id == user_id
        )
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id.in_(session_ids),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )

        return result.rowcount or 0

    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int,
    ) -> list[UserSession]:
        statement = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
            )
            .order_by(
                UserSession.created_at.desc(),
            )
        )

        result = await db.execute(statement)

        return list(result.scalars().all())
