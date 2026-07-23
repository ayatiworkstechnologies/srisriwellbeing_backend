from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.password_reset_model import PasswordResetToken


class PasswordResetRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        reset_token: PasswordResetToken,
    ) -> PasswordResetToken:
        db.add(reset_token)

        await db.flush()
        await db.refresh(reset_token)

        return reset_token

    @staticmethod
    async def get_valid_by_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used.is_(False),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def mark_as_used(
        db: AsyncSession,
        reset_token: PasswordResetToken,
    ) -> None:
        reset_token.is_used = True
        reset_token.used_at = datetime.utcnow()

        await db.flush()

    @staticmethod
    async def invalidate_user_tokens(
        db: AsyncSession,
        user_id: int,
    ) -> None:
        statement = (
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used.is_(False),
            )
            .values(
                is_used=True,
                used_at=datetime.utcnow(),
            )
        )

        await db.execute(statement)
        await db.flush()