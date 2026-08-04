from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.modules.rbac.schema import (
    AssignPermissionsRequest,
    AssignRolesRequest,
    PermissionCreateRequest,
    PermissionUpdateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from app.modules.rbac.service import RBACService

router = APIRouter(
    tags=["RBAC"],
)
RBAC_MANAGEMENT = [Depends(require_permission("rbac.manage"))]

# =========================================================
# ROLE PERMISSION ASSIGNMENT
# =========================================================


@router.post(
    "/roles/{role_id}/permissions",
    summary="Assign permissions to role",
    dependencies=RBAC_MANAGEMENT,
)
async def assign_permissions_to_role(
    payload: AssignPermissionsRequest,
    role_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.assign_permissions_to_role(
        db=db,
        role_id=role_id,
        permission_ids=payload.permission_ids,
    )


# =========================================================
# USER ROLE ASSIGNMENT
# =========================================================


@router.post(
    "/users/{user_id}/roles",
    summary="Assign roles to user",
    dependencies=RBAC_MANAGEMENT,
)
async def assign_roles_to_user(
    payload: AssignRolesRequest,
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.assign_roles_to_user(
        db=db,
        user_id=user_id,
        role_ids=payload.role_ids,
    )


@router.get(
    "/users/{user_id}/roles",
    summary="Get user roles",
    dependencies=RBAC_MANAGEMENT,
)
async def get_user_roles(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.get_user_roles(
        db=db,
        user_id=user_id,
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    summary="Remove role from user",
    dependencies=RBAC_MANAGEMENT,
)
async def remove_role_from_user(
    user_id: int = Path(gt=0),
    role_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.remove_role_from_user(
        db=db,
        user_id=user_id,
        role_id=role_id,
    )


# =========================================================
# ROLES
# =========================================================


@router.post(
    "/roles",
    summary="Create role",
    dependencies=RBAC_MANAGEMENT,
)
async def create_role(
    payload: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.create_role(
        db=db,
        payload=payload,
    )


@router.get(
    "/roles",
    summary="Get roles",
)
async def get_roles(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.get_roles(
        db=db,
    )


@router.get(
    "/roles/{role_id}",
    summary="Get role by ID",
    dependencies=RBAC_MANAGEMENT,
)
async def get_role_by_id(
    role_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.get_role_by_id(
        db=db,
        role_id=role_id,
    )


@router.patch(
    "/roles/{role_id}",
    summary="Update role",
    dependencies=RBAC_MANAGEMENT,
)
async def update_role(
    payload: RoleUpdateRequest,
    role_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.update_role(
        db=db, role_id=role_id, payload=payload
    )


@router.delete(
    "/roles/{role_id}",
    summary="Delete role",
    dependencies=RBAC_MANAGEMENT,
)
async def delete_role(
    role_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.delete_role(db=db, role_id=role_id)


# =========================================================
# PERMISSIONS
# =========================================================


@router.post(
    "/permissions",
    summary="Create permission",
    dependencies=RBAC_MANAGEMENT,
)
async def create_permission(
    payload: PermissionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.create_permission(
        db=db,
        payload=payload,
    )


@router.get(
    "/permissions",
    summary="Get permissions",
    dependencies=RBAC_MANAGEMENT,
)
async def get_permissions(
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.get_permissions(
        db=db,
    )


@router.get(
    "/permissions/{permission_id}",
    summary="Get permission by ID",
    dependencies=RBAC_MANAGEMENT,
)
async def get_permission_by_id(
    permission_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.get_permission_by_id(
        db=db,
        permission_id=permission_id,
    )


@router.patch(
    "/permissions/{permission_id}",
    summary="Update permission",
    dependencies=RBAC_MANAGEMENT,
)
async def update_permission(
    payload: PermissionUpdateRequest,
    permission_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.update_permission(
        db=db,
        permission_id=permission_id,
        payload=payload,
    )


@router.delete(
    "/permissions/{permission_id}",
    summary="Delete permission",
    dependencies=RBAC_MANAGEMENT,
)
async def delete_permission(
    permission_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await RBACService.delete_permission(
        db=db,
        permission_id=permission_id,
    )
