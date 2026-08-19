from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.request_utils import (
    get_client_ip,
    get_user_agent,
)

from app.modules.audit_logs.constants import (
    AuditAction,
)
from app.modules.audit_logs.service import (
    AuditLogService,
)

from app.modules.rbac.schema import (
    AssignRolesRequest,
)
from app.modules.rbac.service import (
    RBACService,
)

from app.modules.users.model import User
from app.modules.users.schema import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.users.service import (
    UserService,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ============================================================
# USER SNAPSHOT FOR AUDIT
# ============================================================


def user_snapshot(
    user: User,
) -> dict[str, Any]:
    """
    Convert safe user fields into JSON-compatible audit data.

    Never include:
    - password
    - password_hash
    - access token
    - refresh token
    """

    user_status = user.status

    if hasattr(
        user_status,
        "value",
    ):
        user_status = (
            user_status.value
        )

    return {
        "id": user.id,
        "full_name":
            user.full_name,
        "email":
            user.email,
        "phone":
            user.phone,
        "status":
            user_status,
        "is_active":
            user.is_active,
        "is_verified":
            user.is_verified,
        "is_deleted":
            user.is_deleted,
    }


# ============================================================
# GET ALL USERS
# ============================================================


@router.get("")
async def get_users(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.view"
        )
    ),
) -> dict:

    users = (
        await UserService
        .get_users(
            db=db,
            skip=skip,
            limit=limit,
        )
    )

    serialized_users = [
        UserResponse
        .model_validate(user)
        .model_dump(
            mode="json"
        )
        for user in users
    ]

    return {
        "success": True,
        "message":
            "Users retrieved successfully",
        "data":
            serialized_users,
    }


# ============================================================
# GET USER BY ID
# ============================================================


@router.get(
    "/{user_id}"
)
async def get_user(
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.view"
        )
    ),
) -> dict:

    user = (
        await UserService
        .get_user(
            db=db,
            user_id=user_id,
        )
    )

    serialized_user = (
        UserResponse
        .model_validate(user)
        .model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message":
            "User retrieved successfully",
        "data":
            serialized_user,
    }


# ============================================================
# CREATE USER
# ============================================================


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.create"
        )
    ),
) -> dict:

    try:
        user = (
            await UserService
            .create_user(
                db=db,
                payload=payload,
            )
        )

        await (
            AuditLogService
            .record(
                db=db,
                user_id=current_user.id,
                action=(
                    AuditAction
                    .USER_CREATED
                ),
                module="users",
                entity_type="User",
                entity_id=user.id,
                description=(
                    f"Created user "
                    f"{user.email}"
                ),
                new_values=(
                    user_snapshot(
                        user
                    )
                ),
                ip_address=(
                    get_client_ip(
                        request
                    )
                ),
                user_agent=(
                    get_user_agent(
                        request
                    )
                ),
            )
        )

        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "message":
                "User created successfully",
            "data": (
                UserResponse
                .model_validate(
                    user
                )
                .model_dump(
                    mode="json"
                )
            ),
        }

    except Exception:
        await db.rollback()
        raise


# ============================================================
# UPDATE USER
# ============================================================


@router.patch(
    "/{user_id}"
)
async def update_user(
    payload: UserUpdateRequest,
    request: Request,
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.update"
        )
    ),
) -> dict:

    try:
        existing_user = (
            await UserService
            .get_user(
                db=db,
                user_id=user_id,
            )
        )

        old_values = (
            user_snapshot(
                existing_user
            )
        )

        updated_user = (
            await UserService
            .update_user(
                db=db,
                user_id=user_id,
                payload=payload,
            )
        )

        new_values = (
            user_snapshot(
                updated_user
            )
        )

        await (
            AuditLogService
            .record(
                db=db,
                user_id=current_user.id,
                action=(
                    AuditAction
                    .USER_UPDATED
                ),
                module="users",
                entity_type="User",
                entity_id=(
                    updated_user.id
                ),
                description=(
                    f"Updated user "
                    f"{updated_user.email}"
                ),
                old_values=(
                    old_values
                ),
                new_values=(
                    new_values
                ),
                ip_address=(
                    get_client_ip(
                        request
                    )
                ),
                user_agent=(
                    get_user_agent(
                        request
                    )
                ),
            )
        )

        await db.commit()

        await db.refresh(
            updated_user
        )

        serialized_user = (
            UserResponse
            .model_validate(
                updated_user
            )
            .model_dump(
                mode="json"
            )
        )

        return {
            "success": True,
            "message":
                "User updated successfully",
            "data":
                serialized_user,
        }

    except Exception:
        await db.rollback()
        raise


# ============================================================
# DELETE USER
# ============================================================


@router.delete(
    "/{user_id}"
)
async def delete_user(
    request: Request,
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.manage"
        )
    ),
) -> dict:

    if (
        current_user.id
        == user_id
    ):
        return {
            "success": False,
            "message":
                "You cannot delete your own account",
        }

    try:
        target_user = (
            await UserService
            .get_user(
                db=db,
                user_id=user_id,
            )
        )

        old_values = (
            user_snapshot(
                target_user
            )
        )

        target_email = (
            target_user.email
        )

        result = (
            await UserService
            .delete_user(
                db=db,
                user_id=user_id,
            )
        )

        await (
            AuditLogService
            .record(
                db=db,
                user_id=current_user.id,
                action=(
                    AuditAction
                    .USER_DELETED
                ),
                module="users",
                entity_type="User",
                entity_id=user_id,
                description=(
                    f"Deleted user "
                    f"{target_email}"
                ),
                old_values=(
                    old_values
                ),
                new_values={
                    "is_active":
                        False,
                    "is_deleted":
                        True,
                },
                ip_address=(
                    get_client_ip(
                        request
                    )
                ),
                user_agent=(
                    get_user_agent(
                        request
                    )
                ),
            )
        )

        await db.commit()

        if isinstance(
            result,
            dict,
        ):
            return result

        return {
            "success": True,
            "message":
                "User deleted successfully",
        }

    except Exception:
        await db.rollback()
        raise


# ============================================================
# ACTIVATE USER
# ============================================================


@router.patch(
    "/{user_id}/activate"
)
async def activate_user(
    request: Request,
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.activate"
        )
    ),
) -> dict:

    try:
        target_user = (
            await UserService
            .get_user(
                db=db,
                user_id=user_id,
            )
        )

        old_values = (
            user_snapshot(
                target_user
            )
        )

        activated_user = (
            await UserService
            .activate_user(
                db=db,
                user_id=user_id,
            )
        )

        new_values = (
            user_snapshot(
                activated_user
            )
        )

        await (
            AuditLogService
            .record(
                db=db,
                user_id=current_user.id,
                action=(
                    AuditAction
                    .USER_ACTIVATED
                ),
                module="users",
                entity_type="User",
                entity_id=(
                    activated_user.id
                ),
                description=(
                    f"Activated user "
                    f"{activated_user.email}"
                ),
                old_values=(
                    old_values
                ),
                new_values=(
                    new_values
                ),
                ip_address=(
                    get_client_ip(
                        request
                    )
                ),
                user_agent=(
                    get_user_agent(
                        request
                    )
                ),
            )
        )

        await db.commit()

        await db.refresh(
            activated_user
        )

        serialized_user = (
            UserResponse
            .model_validate(
                activated_user
            )
            .model_dump(
                mode="json"
            )
        )

        return {
            "success": True,
            "message":
                "User activated successfully",
            "data":
                serialized_user,
        }

    except Exception:
        await db.rollback()
        raise


# ============================================================
# DEACTIVATE USER
# ============================================================


@router.patch(
    "/{user_id}/deactivate"
)
async def deactivate_user(
    request: Request,
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.deactivate"
        )
    ),
) -> dict:

    if (
        current_user.id
        == user_id
    ):
        return {
            "success": False,
            "message": (
                "You cannot deactivate "
                "your own account"
            ),
        }

    try:
        target_user = (
            await UserService
            .get_user(
                db=db,
                user_id=user_id,
            )
        )

        old_values = (
            user_snapshot(
                target_user
            )
        )

        deactivated_user = (
            await UserService
            .deactivate_user(
                db=db,
                user_id=user_id,
            )
        )

        new_values = (
            user_snapshot(
                deactivated_user
            )
        )

        await (
            AuditLogService
            .record(
                db=db,
                user_id=current_user.id,
                action=(
                    AuditAction
                    .USER_DEACTIVATED
                ),
                module="users",
                entity_type="User",
                entity_id=(
                    deactivated_user.id
                ),
                description=(
                    f"Deactivated user "
                    f"{deactivated_user.email}"
                ),
                old_values=(
                    old_values
                ),
                new_values=(
                    new_values
                ),
                ip_address=(
                    get_client_ip(
                        request
                    )
                ),
                user_agent=(
                    get_user_agent(
                        request
                    )
                ),
            )
        )

        await db.commit()

        await db.refresh(
            deactivated_user
        )

        serialized_user = (
            UserResponse
            .model_validate(
                deactivated_user
            )
            .model_dump(
                mode="json"
            )
        )

        return {
            "success": True,
            "message":
                "User deactivated successfully",
            "data":
                serialized_user,
        }

    except Exception:
        await db.rollback()
        raise


# ============================================================
# ASSIGN / REPLACE USER ROLES
# ============================================================


@router.put(
    "/{user_id}/roles"
)
async def assign_roles_to_user(
    payload: AssignRolesRequest,
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.assign_role"
        )
    ),
) -> dict:
    """
    Replace the roles assigned to a user.

    Example:

    {
        "role_ids": [2]
    }
    """

    return await (
        RBACService
        .assign_roles_to_user(
            db=db,
            user_id=user_id,
            role_ids=(
                payload.role_ids
            ),
        )
    )


# ============================================================
# GET USER ROLES
# ============================================================


@router.get(
    "/{user_id}/roles"
)
async def get_user_roles(
    user_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.view"
        )
    ),
) -> dict:
    """
    Get all active roles
    assigned to a user.
    """

    return await (
        RBACService
        .get_user_roles(
            db=db,
            user_id=user_id,
        )
    )


# ============================================================
# REMOVE ONE ROLE FROM USER
# ============================================================


@router.delete(
    "/{user_id}/roles/{role_id}"
)
async def remove_role_from_user(
    user_id: int = Path(
        gt=0
    ),
    role_id: int = Path(
        gt=0
    ),
    db: AsyncSession = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "users.remove_role"
        )
    ),
) -> dict:
    """
    Remove one role
    assigned to a user.
    """

    return await (
        RBACService
        .remove_role_from_user(
            db=db,
            user_id=user_id,
            role_id=role_id,
        )
    )
