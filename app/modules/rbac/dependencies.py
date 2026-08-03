from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.repository import RBACRepository
from app.modules.users.model import User


def require_role(
    *allowed_roles: str,
) -> Callable:
    """
    Allow access when the authenticated user has at least
    one of the supplied roles.

    Example:
        Depends(require_role("admin"))

        Depends(
            require_role(
                "admin",
                "receptionist",
            )
        )
    """

    normalized_roles = {
        role.strip().lower()
        for role in allowed_roles
        if role and role.strip()
    }

    if not normalized_roles:
        raise ValueError(
            "At least one allowed role must be configured"
        )

    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        for role_name in normalized_roles:
            has_role = await RBACRepository.user_has_role(
                db=db,
                user_id=current_user.id,
                role_name=role_name,
            )

            if has_role:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": (
                    "You do not have permission "
                    "to access this resource"
                ),
                "required_roles": sorted(
                    normalized_roles
                ),
            },
        )

    return role_checker


def require_permission(
    *permission_codes: str,
    require_all: bool = True,
) -> Callable:
    """
    Validate one or more permissions.

    By default, all supplied permissions are required.

    Examples:
        Depends(
            require_permission(
                "patient.dashboard.view"
            )
        )

        Depends(
            require_permission(
                "patient.profile.read",
                "patient.profile.update",
            )
        )

        Depends(
            require_permission(
                "patients.read",
                "patients.create",
                require_all=False,
            )
        )
    """

    normalized_permissions = {
        permission_code.strip().lower()
        for permission_code in permission_codes
        if permission_code
        and permission_code.strip()
    }

    if not normalized_permissions:
        raise ValueError(
            "At least one permission must be configured"
        )

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        permission_results: dict[str, bool] = {}

        for permission_code in normalized_permissions:
            permission_results[permission_code] = (
                await RBACRepository.user_has_permission(
                    db=db,
                    user_id=current_user.id,
                    permission_code=permission_code,
                )
            )

        if require_all:
            is_allowed = all(
                permission_results.values()
            )
        else:
            is_allowed = any(
                permission_results.values()
            )

        if is_allowed:
            return current_user

        missing_permissions = [
            permission_code
            for permission_code, has_permission
            in permission_results.items()
            if not has_permission
        ]

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": (
                    "You do not have the required "
                    "permission"
                ),
                "required_permissions": sorted(
                    normalized_permissions
                ),
                "missing_permissions": sorted(
                    missing_permissions
                ),
                "require_all": require_all,
            },
        )

    return permission_checker