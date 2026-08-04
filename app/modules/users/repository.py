from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.model import User


class UserRepository:

    @staticmethod
    async def get_by_email(
        db: AsyncSession,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.email == email.lower().strip(),
            User.is_deleted.is_(False),
        )

        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(
        db: AsyncSession,
        phone: str,
    ) -> User | None:
        statement = select(User).where(
            User.phone == phone,
        )

        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.is_deleted.is_(False),
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def save(
        db: AsyncSession,
        user: User,
    ) -> User:
        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def create(
        db: AsyncSession,
        user: User,
    ) -> User:
        db.add(user)

        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def update_password(
        db: AsyncSession,
        user: User,
        password_hash: str,
    ) -> User:
        user.password_hash = password_hash
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None

        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        result = await db.execute(
            select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.id.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())
