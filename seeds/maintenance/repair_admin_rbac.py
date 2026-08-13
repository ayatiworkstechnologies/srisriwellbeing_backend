"""Repair RBAC assignments for an existing administrator account."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.modules.rbac.model import Permission, Role, RolePermission, UserRole
from app.modules.users.model import User

REQUIRED_ADMIN_PERMISSIONS = (
    ("users.view", "View Users", "users"),
    ("users.list", "List Users", "users"),
    ("users.manage", "Manage Users", "users"),
    ("rbac.manage", "Manage RBAC", "rbac"),
    ("roles.view", "View Roles", "roles"),
    ("roles.list", "List Roles", "roles"),
    ("roles.manage", "Manage Roles", "roles"),
    ("permissions.view", "View Permissions", "permissions"),
    ("permissions.list", "List Permissions", "permissions"),
    ("permissions.manage", "Manage Permissions", "permissions"),
)


def columns(model: type[Any]) -> set[str]:
    return {column.key for column in model.__table__.columns}


def supported(model: type[Any], values: dict[str, Any]) -> dict[str, Any]:
    available = columns(model)
    return {key: value for key, value in values.items() if key in available}


def role_key_column() -> Any:
    if "name" in columns(Role):
        return Role.name
    if "code" in columns(Role):
        return Role.code
    raise RuntimeError("Role model must contain name or code")


def permission_key_column() -> Any:
    if "code" in columns(Permission):
        return Permission.code
    if "name" in columns(Permission):
        return Permission.name
    raise RuntimeError("Permission model must contain code or name")


async def get_admin_role(db: AsyncSession) -> Role:
    key = role_key_column()
    result = await db.execute(select(Role).where(key == "admin"))
    role = result.scalar_one_or_none()

    if role is None:
        role = Role(**supported(Role, {
            "name": "admin",
            "code": "admin",
            "display_name": "Admin",
            "description": "System administrator",
            "is_system": True,
            "is_system_role": True,
            "is_active": True,
        }))
        db.add(role)
        await db.flush()

    return role


async def get_admin_user(db: AsyncSession, email: str) -> User:
    result = await db.execute(
        select(User).where(User.email == email.strip().lower())
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise RuntimeError(
            f"Admin user '{email}' does not exist. "
            "Create the administrator account first."
        )
    return user


async def ensure_user_role(db: AsyncSession, user: User, role: Role) -> int:
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        if "is_active" in columns(UserRole):
            mapping.is_active = True
        return 0

    db.add(UserRole(**supported(UserRole, {
        "user_id": user.id,
        "role_id": role.id,
        "is_active": True,
    })))
    return 1


async def ensure_permission(
    db: AsyncSession,
    code: str,
    display_name: str,
    module: str,
) -> Permission:
    key = permission_key_column()
    result = await db.execute(select(Permission).where(key == code))
    row = result.scalar_one_or_none()

    values = {
        "code": code,
        "name": code if key.key == "name" else display_name,
        "display_name": display_name,
        "module": module,
        "description": display_name,
        "is_system": True,
        "is_system_permission": True,
        "is_active": True,
    }

    if row is None:
        row = Permission(**supported(Permission, values))
        db.add(row)
        await db.flush()
    else:
        for field, value in supported(Permission, values).items():
            if field not in {"id", key.key}:
                setattr(row, field, value)

    return row


async def ensure_role_permission(
    db: AsyncSession,
    role: Role,
    permission: Permission,
) -> int:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        if "is_active" in columns(RolePermission):
            mapping.is_active = True
        return 0

    db.add(RolePermission(**supported(RolePermission, {
        "role_id": role.id,
        "permission_id": permission.id,
        "is_active": True,
    })))
    return 1


async def repair(email: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            try:
                role = await get_admin_role(db)
                user = await get_admin_user(db, email)
                user_role_created = await ensure_user_role(db, user, role)

                mappings_created = 0
                for code, display_name, module in REQUIRED_ADMIN_PERMISSIONS:
                    permission = await ensure_permission(
                        db, code, display_name, module
                    )
                    mappings_created += await ensure_role_permission(
                        db, role, permission
                    )

                await db.commit()
                print(
                    "Admin RBAC repaired | "
                    f"user_role_created={user_role_created} | "
                    f"mappings_created={mappings_created}"
                )
            except Exception:
                await db.rollback()
                raise
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    asyncio.run(repair(args.email))


if __name__ == "__main__":
    main()
