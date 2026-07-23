from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import UserSession


class AuthRepository:
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