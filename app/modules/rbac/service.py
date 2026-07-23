from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rbac.model import Permission, Role
from app.modules.rbac.repository import RBACRepository
from app.modules.rbac.schema import (
    PermissionCreateRequest,
    RoleCreateRequest,
)
from app.modules.users.repository import UserRepository


class RBACService:

    @staticmethod
    async def get_roles(
        db: AsyncSession,
    ) -> dict:
        roles = await RBACRepository.get_roles(db=db)

        return {
            "success": True,
            "message": "Roles retrieved successfully",
            "data": [
                {
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.display_name,
                    "description": role.description,
                    "is_system": role.is_system,
                    "is_active": role.is_active,
                    "permission_count": len(role.permissions),
                    "created_at": role.created_at,
                    "updated_at": role.updated_at,
                }
                for role in roles
            ],
        }

    @staticmethod
    async def get_role_by_id(
        db: AsyncSession,
        role_id: int,
    ) -> dict:
        role = await RBACRepository.get_role_by_id(
            db=db,
            role_id=role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        return {
            "success": True,
            "message": "Role retrieved successfully",
            "data": {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "is_system": role.is_system,
                "is_active": role.is_active,
                "permissions": [
                    {
                        "id": permission.id,
                        "module": permission.module,
                        "action": permission.action,
                        "code": permission.code,
                        "description": permission.description,
                        "is_active": permission.is_active,
                    }
                    for permission in role.permissions
                ],
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            },
        }

    @staticmethod
    async def get_permissions(
        db: AsyncSession,
    ) -> dict:
        permissions = await RBACRepository.get_permissions(db=db)

        return {
            "success": True,
            "message": "Permissions retrieved successfully",
            "data": [
                {
                    "id": permission.id,
                    "module": permission.module,
                    "action": permission.action,
                    "code": permission.code,
                    "description": permission.description,
                    "is_active": permission.is_active,
                    "created_at": permission.created_at,
                    "updated_at": permission.updated_at,
                }
                for permission in permissions
            ],
        }

    @staticmethod
    async def get_permission_by_id(
        db: AsyncSession,
        permission_id: int,
    ) -> dict:
        permission = await RBACRepository.get_permission_by_id(
            db=db,
            permission_id=permission_id,
        )

        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )

        return {
            "success": True,
            "message": "Permission retrieved successfully",
            "data": {
                "id": permission.id,
                "module": permission.module,
                "action": permission.action,
                "code": permission.code,
                "description": permission.description,
                "is_active": permission.is_active,
                "created_at": permission.created_at,
                "updated_at": permission.updated_at,
            },
        }

    @staticmethod
    async def create_role(
        db: AsyncSession,
        payload: RoleCreateRequest,
    ) -> dict:
        role_name = payload.name.strip().lower()

        existing_role = await RBACRepository.get_role_by_name(
            db=db,
            name=role_name,
        )

        if existing_role is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already exists",
            )

        role = Role(
            name=role_name,
            display_name=payload.display_name.strip(),
            description=(
                payload.description.strip()
                if payload.description
                else None
            ),
            is_system=False,
            is_active=payload.is_active,
        )

        try:
            created_role = await RBACRepository.create_role(
                db=db,
                role=role,
            )

            await db.commit()
            await db.refresh(created_role)

        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already exists",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Role created successfully",
            "data": {
                "id": created_role.id,
                "name": created_role.name,
                "display_name": created_role.display_name,
                "description": created_role.description,
                "is_system": created_role.is_system,
                "is_active": created_role.is_active,
            },
        }

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        payload: PermissionCreateRequest,
    ) -> dict:
        module = payload.module.strip().lower()
        action = payload.action.strip().lower()
        permission_code = f"{module}.{action}"

        existing_permission = (
            await RBACRepository.get_permission_by_code(
                db=db,
                code=permission_code,
            )
        )

        if existing_permission is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission already exists",
            )

        permission = Permission(
            module=module,
            action=action,
            code=permission_code,
            description=(
                payload.description.strip()
                if payload.description
                else None
            ),
            is_active=True,
        )

        try:
            created_permission = (
                await RBACRepository.create_permission(
                    db=db,
                    permission=permission,
                )
            )

            await db.commit()
            await db.refresh(created_permission)

        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission already exists",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Permission created successfully",
            "data": {
                "id": created_permission.id,
                "module": created_permission.module,
                "action": created_permission.action,
                "code": created_permission.code,
                "description": created_permission.description,
                "is_active": created_permission.is_active,
            },
        }

    @staticmethod
    async def assign_permissions_to_role(
        db: AsyncSession,
        role_id: int,
        permission_ids: list[int],
    ) -> dict:
        role = await RBACRepository.get_role_by_id(
            db=db,
            role_id=role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        unique_permission_ids = list(dict.fromkeys(permission_ids))

        permissions = await RBACRepository.get_permissions_by_ids(
            db=db,
            permission_ids=unique_permission_ids,
        )

        found_permission_ids = {
            permission.id for permission in permissions
        }

        missing_permission_ids = [
            permission_id
            for permission_id in unique_permission_ids
            if permission_id not in found_permission_ids
        ]

        if missing_permission_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": (
                        "Some permissions were not found or are inactive"
                    ),
                    "permission_ids": missing_permission_ids,
                },
            )

        try:
            await RBACRepository.replace_role_permissions(
                db=db,
                role_id=role.id,
                permission_ids=unique_permission_ids,
            )
            await db.commit()

        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to assign permissions to role",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        permission_by_id = {
            permission.id: permission
            for permission in permissions
        }

        ordered_permissions = [
            permission_by_id[permission_id]
            for permission_id in unique_permission_ids
            if permission_id in permission_by_id
        ]

        return {
            "success": True,
            "message": "Permissions assigned to role successfully",
            "data": {
                "role_id": role.id,
                "role_name": role.name,
                "permissions": [
                    {
                        "id": permission.id,
                        "module": permission.module,
                        "action": permission.action,
                        "code": permission.code,
                        "description": permission.description,
                        "is_active": permission.is_active,
                    }
                    for permission in ordered_permissions
                ],
            },
        }
    @staticmethod
    async def assign_roles_to_user(
        db: AsyncSession,
        user_id: int,
        role_ids: list[int],
    ) -> dict:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        unique_role_ids = list(dict.fromkeys(role_ids))

        roles = await RBACRepository.get_roles_by_ids(
            db=db,
            role_ids=unique_role_ids,
        )

        found_role_ids = {role.id for role in roles}

        missing_role_ids = [
            role_id
            for role_id in unique_role_ids
            if role_id not in found_role_ids
        ]

        if missing_role_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Some roles were not found or are inactive",
                    "role_ids": missing_role_ids,
                },
            )

        try:
            await RBACRepository.replace_user_roles(
                db=db,
                user_id=user.id,
                role_ids=unique_role_ids,
            )
            await db.commit()

        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to assign roles to user",
            ) from exc

        except Exception:
            await db.rollback()
            raise

        role_by_id = {role.id: role for role in roles}

        ordered_roles = [
            role_by_id[role_id]
            for role_id in unique_role_ids
            if role_id in role_by_id
        ]

        return {
            "success": True,
            "message": "Roles assigned to user successfully",
            "data": {
                "user_id": user.id,
                "email": user.email,
                "roles": [
                    {
                        "id": role.id,
                        "name": role.name,
                        "display_name": role.display_name,
                        "is_active": role.is_active,
                    }
                    for role in ordered_roles
                ],
            },
        }

    @staticmethod
    async def get_user_roles(
        db: AsyncSession,
        user_id: int,
    ) -> dict:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        roles = await RBACRepository.get_user_roles(
            db=db,
            user_id=user_id,
        )

        return {
            "success": True,
            "message": "User roles retrieved successfully",
            "data": {
                "user_id": user.id,
                "email": user.email,
                "roles": [
                    {
                        "id": role.id,
                        "name": role.name,
                        "display_name": role.display_name,
                        "description": role.description,
                        "is_active": role.is_active,
                    }
                    for role in roles
                ],
            },
        }

    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user_id: int,
        role_id: int,
    ) -> dict:
        user = await UserRepository.get_by_id(
            db=db,
            user_id=user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        role = await RBACRepository.get_role_by_id(
            db=db,
            role_id=role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        try:
            removed = await RBACRepository.remove_role_from_user(
                db=db,
                user_id=user_id,
                role_id=role_id,
            )

            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role is not assigned to this user",
                )

            await db.commit()

        except HTTPException:
            await db.rollback()
            raise

        except Exception:
            await db.rollback()
            raise

        return {
            "success": True,
            "message": "Role removed from user successfully",
            "data": {
                "user_id": user_id,
                "role_id": role_id,
            },
        }