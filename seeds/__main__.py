"""Run every application seed in its required dependency order."""

from __future__ import annotations

import asyncio
import logging

from app.core.database import AsyncSessionLocal, engine
from seeds.permissions_seed import seed_permissions
from seeds.role_permissions_seed import seed_role_permissions
from seeds.roles_seed import seed_roles

logger = logging.getLogger(__name__)


async def seed_all() -> dict[str, dict[str, int]]:
    """Create/update roles and permissions, then synchronize mappings."""
    async with AsyncSessionLocal() as db:
        roles = await seed_roles(db)
        permissions = await seed_permissions(db)
        mappings = await seed_role_permissions(db)

    return {
        "roles": roles,
        "permissions": permissions,
        "role_permissions": mappings,
    }


async def main() -> None:
    try:
        result = await seed_all()
    finally:
        await engine.dispose()

    logger.info("Application seed completed: %s", result)
    print(
        "Application seed completed | "
        f"roles={result['roles']['total']} | "
        f"permissions={result['permissions']['total']} | "
        f"mappings_created={result['role_permissions']['created']} | "
        f"mappings_deleted={result['role_permissions']['deleted']}"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(main())
