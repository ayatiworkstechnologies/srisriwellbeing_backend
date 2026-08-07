from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.main import app
from app.modules.auth.password_reset_repository import PasswordResetRepository
from app.modules.users.repository import UserRepository
from app.modules.auth.service import AuthService
from app.modules.auth.token_service import TokenService

_ = app  # Initialize the complete SQLAlchemy model registry.


@pytest.mark.asyncio
async def test_forgot_password_hides_token_outside_development(
    monkeypatch,
) -> None:
    db = SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    user = SimpleNamespace(id=42, is_active=True)
    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(
        PasswordResetRepository,
        "invalidate_user_tokens",
        AsyncMock(),
    )
    create_token = AsyncMock()
    monkeypatch.setattr(
        PasswordResetRepository,
        "create",
        create_token,
    )
    monkeypatch.setattr(
        TokenService,
        "create_password_reset_token",
        lambda: "raw-secret-token",
    )
    monkeypatch.setattr(
        TokenService,
        "hash_password_reset_token",
        lambda token: f"hashed:{token}",
    )
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "PASSWORD_RESET_EXPIRE_MINUTES", 17)
    started_at = datetime.now()

    response = await AuthService.forgot_password(
        db=db,
        email=" PATIENT@EXAMPLE.COM ",
    )

    assert response["success"] is True
    assert "development_data" not in response
    UserRepository.get_by_email.assert_awaited_once_with(
        db=db,
        email="patient@example.com",
    )
    reset_token = create_token.await_args.kwargs["reset_token"]
    assert reset_token.token_hash == "hashed:raw-secret-token"
    expected_expiry = started_at + timedelta(minutes=17)
    assert abs((reset_token.expires_at - expected_expiry).total_seconds()) < 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_forgot_password_exposes_token_only_in_development(
    monkeypatch,
) -> None:
    db = SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=SimpleNamespace(id=42, is_active=True)),
    )
    monkeypatch.setattr(
        PasswordResetRepository,
        "invalidate_user_tokens",
        AsyncMock(),
    )
    monkeypatch.setattr(
        PasswordResetRepository,
        "create",
        AsyncMock(),
    )
    monkeypatch.setattr(
        TokenService,
        "create_password_reset_token",
        lambda: "development-token",
    )
    monkeypatch.setattr(
        TokenService,
        "hash_password_reset_token",
        lambda token: f"hashed:{token}",
    )
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "PASSWORD_RESET_EXPIRE_MINUTES", 23)

    response = await AuthService.forgot_password(
        db=db,
        email="patient@example.com",
    )

    assert response["development_data"] == {
        "reset_token": "development-token",
        "expires_in_minutes": 23,
    }
