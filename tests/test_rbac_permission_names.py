from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.rbac.repository import RBACRepository
from app.modules.rbac.service import RBACService


@pytest.mark.asyncio
async def test_permission_list_returns_human_readable_name(
    monkeypatch,
) -> None:
    now = datetime.now()
    permission = SimpleNamespace(
        id=99,
        name="Acknowledge Allergy Alert",
        module="allergy",
        action="acknowledge_alert",
        code="allergy.acknowledge_alert",
        description="Record that an allergy warning was reviewed.",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    get_permissions = AsyncMock(return_value=[permission])
    monkeypatch.setattr(
        RBACRepository,
        "get_permissions",
        get_permissions,
    )
    db = object()

    result = await RBACService.get_permissions(db=db)

    assert result["data"][0]["name"] == "Acknowledge Allergy Alert"
    get_permissions.assert_awaited_once_with(db=db)
