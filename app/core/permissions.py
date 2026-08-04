from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User


def require_permission(
    permission_code: str,
) -> Callable:
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        has_permission = await RBACRepository.user_has_permission(
            db=db,
            user_id=current_user.id,
            permission_code=permission_code,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(f"Permission required: " f"{permission_code}"),
            )

        return current_user

    return permission_checker


def require_role(
    role_name: str,
) -> Callable:
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        has_role = await RBACRepository.user_has_role(
            db=db,
            user_id=current_user.id,
            role_name=role_name,
        )

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}",
            )

        return current_user

    return role_checker
