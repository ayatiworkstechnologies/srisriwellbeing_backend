from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rbac.association import RolePermission, UserRole
from app.modules.rbac.model import Permission, Role


class RBACRepository:
    @staticmethod
    async def delete_role(db: AsyncSession, role: Role) -> None:
        await db.delete(role)
        await db.flush()

    @staticmethod
    async def delete_permission(
        db: AsyncSession,
        permission: Permission,
    ) -> None:
        await db.delete(permission)
        await db.flush()

    @staticmethod
    async def get_permissions_by_ids(
        db: AsyncSession,
        permission_ids: list[int],
    ) -> list[Permission]:
        if not permission_ids:
            return []

        result = await db.execute(
            select(Permission).where(
                Permission.id.in_(permission_ids),
                Permission.is_active.is_(True),
            )
        )

        return list(result.scalars().all())

    @staticmethod
    async def replace_role_permissions(
        db: AsyncSession,
        role_id: int,
        permission_ids: list[int],
    ) -> None:
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )

        for permission_id in permission_ids:
            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )

    @staticmethod
    async def create_role(
        db: AsyncSession,
        role: Role,
    ) -> Role:
        db.add(role)

        await db.flush()
        await db.refresh(role)

        return role

    @staticmethod
    async def get_role_by_id(
        db: AsyncSession,
        role_id: int,
    ) -> Role | None:
        statement = (
            select(Role)
            .options(
                selectinload(Role.permissions),
            )
            .where(
                Role.id == role_id,
            )
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_role_by_name(
        db: AsyncSession,
        name: str,
    ) -> Role | None:
        statement = select(Role).where(
            Role.name == name,
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_roles(
        db: AsyncSession,
    ) -> list[Role]:
        statement = (
            select(Role)
            .options(
                selectinload(Role.permissions),
            )
            .order_by(Role.id.asc())
        )

        result = await db.execute(statement)

        return list(result.scalars().unique().all())

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        permission: Permission,
    ) -> Permission:
        db.add(permission)

        await db.flush()
        await db.refresh(permission)

        return permission

    @staticmethod
    async def get_permission_by_code(
        db: AsyncSession,
        code: str,
    ) -> Permission | None:
        statement = select(Permission).where(
            Permission.code == code,
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_permission_by_id(
        db: AsyncSession,
        permission_id: int,
    ) -> Permission | None:
        statement = select(Permission).where(
            Permission.id == permission_id,
        )

        result = await db.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_permissions(
        db: AsyncSession,
    ) -> list[Permission]:
        statement = select(Permission).order_by(
            Permission.module.asc(),
            Permission.action.asc(),
        )

        result = await db.execute(statement)

        return list(result.scalars().all())

    @staticmethod
    async def get_roles_by_ids(
        db: AsyncSession,
        role_ids: list[int],
    ) -> list[Role]:
        if not role_ids:
            return []

        result = await db.execute(
            select(Role).where(
                Role.id.in_(role_ids),
                Role.is_active.is_(True),
            )
        )

        return list(result.scalars().all())

    @staticmethod
    async def replace_user_roles(
        db: AsyncSession,
        user_id: int,
        role_ids: list[int],
    ) -> None:
        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))

        for role_id in role_ids:
            db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role_id,
                )
            )

    @staticmethod
    async def get_user_roles(
        db: AsyncSession,
        user_id: int,
    ) -> list[Role]:
        result = await db.execute(
            select(Role)
            .join(
                UserRole,
                UserRole.role_id == Role.id,
            )
            .options(selectinload(Role.permissions))
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
            )
            .order_by(Role.id.asc())
        )

        return list(result.scalars().unique().all())

    @staticmethod
    async def get_user_permissions(
        db: AsyncSession,
        user_id: int,
    ) -> list[Permission]:
        result = await db.execute(
            select(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(
                UserRole,
                UserRole.role_id == RolePermission.role_id,
            )
            .join(
                Role,
                Role.id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
                Permission.is_active.is_(True),
            )
            .order_by(Permission.code.asc())
        )

        return list(result.scalars().unique().all())

    @staticmethod
    async def user_has_permission(
        db: AsyncSession,
        user_id: int,
        permission_code: str,
    ) -> bool:
        result = await db.execute(
            select(Permission.id)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(
                UserRole,
                UserRole.role_id == RolePermission.role_id,
            )
            .join(
                Role,
                Role.id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user_id,
                Permission.code == permission_code,
                Permission.is_active.is_(True),
                Role.is_active.is_(True),
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    @staticmethod
    async def user_has_role(
        db: AsyncSession,
        user_id: int,
        role_name: str,
    ) -> bool:
        result = await db.execute(
            select(Role.id)
            .join(
                UserRole,
                UserRole.role_id == Role.id,
            )
            .where(
                UserRole.user_id == user_id,
                Role.name == role_name.strip().lower(),
                Role.is_active.is_(True),
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None
