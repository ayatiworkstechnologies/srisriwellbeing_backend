from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rbac.association import (
    RolePermission,
    UserRole,
)
from app.modules.rbac.model import (
    Permission,
    Role,
)


class RBACRepository:

    # =========================================================
    # ROLE DELETE
    # =========================================================

    @staticmethod
    async def delete_role(
        db: AsyncSession,
        role: Role,
    ) -> None:
        await db.delete(role)
        await db.flush()

    # =========================================================
    # PERMISSION DELETE
    # =========================================================

    @staticmethod
    async def delete_permission(
        db: AsyncSession,
        permission: Permission,
    ) -> None:
        await db.delete(permission)
        await db.flush()

    # =========================================================
    # GET PERMISSIONS BY IDS
    # =========================================================

    @staticmethod
    async def get_permissions_by_ids(
        db: AsyncSession,
        permission_ids: list[int],
    ) -> list[Permission]:

        if not permission_ids:
            return []

        unique_ids = list(
            dict.fromkeys(
                permission_ids
            )
        )

        result = await db.execute(
            select(Permission).where(
                Permission.id.in_(
                    unique_ids
                ),
                Permission.is_active.is_(
                    True
                ),
            )
        )

        return list(
            result.scalars().all()
        )

    # =========================================================
    # REPLACE ROLE PERMISSIONS
    # =========================================================

    @staticmethod
    async def replace_role_permissions(
        db: AsyncSession,
        role_id: int,
        permission_ids: list[int],
    ) -> None:

        await db.execute(
            delete(
                RolePermission
            ).where(
                RolePermission.role_id
                == role_id
            )
        )

        unique_permission_ids = list(
            dict.fromkeys(
                permission_ids
            )
        )

        for permission_id in (
            unique_permission_ids
        ):
            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )

        await db.flush()

    # =========================================================
    # CREATE ROLE
    # =========================================================

    @staticmethod
    async def create_role(
        db: AsyncSession,
        role: Role,
    ) -> Role:

        db.add(role)

        await db.flush()
        await db.refresh(role)

        return role

    # =========================================================
    # GET ROLE BY ID
    # =========================================================

    @staticmethod
    async def get_role_by_id(
        db: AsyncSession,
        role_id: int,
    ) -> Role | None:

        statement = (
            select(Role)
            .options(
                selectinload(
                    Role.permissions
                )
            )
            .where(
                Role.id == role_id
            )
        )

        result = await db.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
        )

    # =========================================================
    # GET ROLE BY NAME
    # =========================================================

    @staticmethod
    async def get_role_by_name(
        db: AsyncSession,
        name: str,
    ) -> Role | None:

        normalized_name = (
            name.strip().lower()
        )

        statement = select(
            Role
        ).where(
            Role.name
            == normalized_name
        )

        result = await db.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
        )

    # =========================================================
    # GET ALL ROLES
    # =========================================================

    @staticmethod
    async def get_roles(
        db: AsyncSession,
    ) -> list[Role]:

        statement = (
            select(Role)
            .options(
                selectinload(
                    Role.permissions
                )
            )
            .order_by(
                Role.id.asc()
            )
        )

        result = await db.execute(
            statement
        )

        return list(
            result
            .scalars()
            .unique()
            .all()
        )

    # =========================================================
    # CREATE PERMISSION
    # =========================================================

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        permission: Permission,
    ) -> Permission:

        db.add(permission)

        await db.flush()
        await db.refresh(
            permission
        )

        return permission

    # =========================================================
    # GET PERMISSION BY CODE
    # =========================================================

    @staticmethod
    async def get_permission_by_code(
        db: AsyncSession,
        code: str,
    ) -> Permission | None:

        normalized_code = (
            code.strip()
        )

        statement = select(
            Permission
        ).where(
            Permission.code
            == normalized_code
        )

        result = await db.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
        )

    # =========================================================
    # GET PERMISSION BY ID
    # =========================================================

    @staticmethod
    async def get_permission_by_id(
        db: AsyncSession,
        permission_id: int,
    ) -> Permission | None:

        statement = select(
            Permission
        ).where(
            Permission.id
            == permission_id
        )

        result = await db.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
        )

    # =========================================================
    # GET ALL PERMISSIONS
    # =========================================================

    @staticmethod
    async def get_permissions(
        db: AsyncSession,
    ) -> list[Permission]:

        statement = (
            select(Permission)
            .order_by(
                Permission.module.asc(),
                Permission.action.asc(),
            )
        )

        result = await db.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    # =========================================================
    # GET ROLES BY IDS
    # =========================================================

    @staticmethod
    async def get_roles_by_ids(
        db: AsyncSession,
        role_ids: list[int],
    ) -> list[Role]:

        if not role_ids:
            return []

        unique_role_ids = list(
            dict.fromkeys(
                role_ids
            )
        )

        result = await db.execute(
            select(Role)
            .options(
                selectinload(
                    Role.permissions
                )
            )
            .where(
                Role.id.in_(
                    unique_role_ids
                ),
                Role.is_active.is_(
                    True
                ),
            )
            .order_by(
                Role.id.asc()
            )
        )

        return list(
            result
            .scalars()
            .unique()
            .all()
        )

    # =========================================================
    # DELETE ALL USER ROLES
    # =========================================================

    @staticmethod
    async def delete_user_roles(
        db: AsyncSession,
        user_id: int,
    ) -> None:

        await db.execute(
            delete(
                UserRole
            ).where(
                UserRole.user_id
                == user_id
            )
        )

        await db.flush()

    # =========================================================
    # ADD USER ROLES
    # =========================================================

    @staticmethod
    async def add_user_roles(
        db: AsyncSession,
        user_id: int,
        role_ids: list[int],
    ) -> None:

        unique_role_ids = list(
            dict.fromkeys(
                role_ids
            )
        )

        for role_id in (
            unique_role_ids
        ):
            db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role_id,
                )
            )

        await db.flush()

    # =========================================================
    # REMOVE ONE ROLE FROM USER
    # =========================================================

    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession,
        user_id: int,
        role_id: int,
    ) -> bool:

        result = await db.execute(
            delete(UserRole).where(
                UserRole.user_id
                == user_id,
                UserRole.role_id
                == role_id,
            )
        )

        await db.flush()

        rowcount = getattr(
            result,
            "rowcount",
            0,
        )

        return bool(
            rowcount
            and rowcount > 0
        )

    # =========================================================
    # REPLACE USER ROLES
    # =========================================================

    @staticmethod
    async def replace_user_roles(
        db: AsyncSession,
        user_id: int,
        role_ids: list[int],
    ) -> list[Role]:

        unique_role_ids = list(
            dict.fromkeys(
                role_ids
            )
        )

        if not unique_role_ids:
            raise ValueError(
                "At least one role is required."
            )

        roles = (
            await RBACRepository
            .get_roles_by_ids(
                db=db,
                role_ids=unique_role_ids,
            )
        )

        if (
            len(roles)
            != len(unique_role_ids)
        ):
            raise ValueError(
                "One or more roles are invalid or inactive."
            )

        await (
            RBACRepository
            .delete_user_roles(
                db=db,
                user_id=user_id,
            )
        )

        await (
            RBACRepository
            .add_user_roles(
                db=db,
                user_id=user_id,
                role_ids=unique_role_ids,
            )
        )

        return roles

    # =========================================================
    # GET USER ROLES
    # =========================================================

    @staticmethod
    async def get_user_roles(
        db: AsyncSession,
        user_id: int,
    ) -> list[Role]:

        result = await db.execute(
            select(Role)
            .join(
                UserRole,
                UserRole.role_id
                == Role.id,
            )
            .options(
                selectinload(
                    Role.permissions
                )
            )
            .where(
                UserRole.user_id
                == user_id,
                Role.is_active.is_(
                    True
                ),
            )
            .order_by(
                Role.id.asc()
            )
        )

        return list(
            result
            .scalars()
            .unique()
            .all()
        )

    # =========================================================
    # GET USER PERMISSIONS
    # =========================================================

    @staticmethod
    async def get_user_permissions(
        db: AsyncSession,
        user_id: int,
    ) -> list[Permission]:

        result = await db.execute(
            select(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id,
            )
            .join(
                UserRole,
                UserRole.role_id
                == RolePermission.role_id,
            )
            .join(
                Role,
                Role.id
                == UserRole.role_id,
            )
            .where(
                UserRole.user_id
                == user_id,
                Role.is_active.is_(
                    True
                ),
                Permission.is_active.is_(
                    True
                ),
            )
            .order_by(
                Permission.code.asc()
            )
        )

        return list(
            result
            .scalars()
            .unique()
            .all()
        )

    # =========================================================
    # CHECK USER PERMISSION
    # =========================================================

    @staticmethod
    async def user_has_permission(
        db: AsyncSession,
        user_id: int,
        permission_code: str,
    ) -> bool:

        normalized_code = (
            permission_code.strip()
        )

        result = await db.execute(
            select(
                Permission.id
            )
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id,
            )
            .join(
                UserRole,
                UserRole.role_id
                == RolePermission.role_id,
            )
            .join(
                Role,
                Role.id
                == UserRole.role_id,
            )
            .where(
                UserRole.user_id
                == user_id,
                Permission.code
                == normalized_code,
                Permission.is_active.is_(
                    True
                ),
                Role.is_active.is_(
                    True
                ),
            )
            .limit(1)
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    # =========================================================
    # CHECK USER ROLE
    # =========================================================

    @staticmethod
    async def user_has_role(
        db: AsyncSession,
        user_id: int,
        role_name: str,
    ) -> bool:

        normalized_name = (
            role_name
            .strip()
            .lower()
        )

        result = await db.execute(
            select(
                Role.id
            )
            .join(
                UserRole,
                UserRole.role_id
                == Role.id,
            )
            .where(
                UserRole.user_id
                == user_id,
                Role.name
                == normalized_name,
                Role.is_active.is_(
                    True
                ),
            )
            .limit(1)
        )

        return (
            result.scalar_one_or_none()
            is not None
        )