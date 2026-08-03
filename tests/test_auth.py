from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.auth.schema import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.auth.token_service import TokenService
from app.modules.users.model import UserStatus


def test_register_requires_positive_role_id() -> None:
    valid_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "+919876543210",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!",
    }

    with pytest.raises(ValidationError):
        RegisterRequest(**valid_payload)

    with pytest.raises(ValidationError):
        RegisterRequest(**valid_payload, role_id=0)


def test_login_requires_positive_role_id() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="test@example.com",
            password="StrongPass1!",
        )

    payload = LoginRequest(
        email="TEST@EXAMPLE.COM",
        password="StrongPass1!",
        role_id=2,
    )

    assert payload.email == "test@example.com"
    assert payload.role_id == 2


def test_tokens_preserve_selected_role_id() -> None:
    access_token = TokenService.create_access_token(
        user_id=10,
        email="test@example.com",
        session_id=20,
        role_id=3,
        roles=["doctor"],
        permissions=["patients.read"],
    )
    refresh_token = TokenService.create_refresh_token(
        user_id=10,
        session_id=20,
        role_id=3,
    )

    access_payload = TokenService.decode_token(access_token)
    refresh_payload = TokenService.decode_token(refresh_token)

    assert access_payload["role_id"] == 3
    assert access_payload["roles"] == ["doctor"]
    assert access_payload["permissions"] == ["patients.read"]
    assert refresh_payload["role_id"] == 3


@pytest.mark.asyncio
async def test_login_rejects_role_not_assigned_to_user() -> None:
    user = SimpleNamespace(
        id=10,
        email="test@example.com",
        password_hash="hash",
        status=UserStatus.ACTIVE.value,
        locked_until=None,
        failed_login_attempts=0,
        is_active=True,
    )
    assigned_role = SimpleNamespace(
        id=2,
        name="doctor",
        is_active=True,
        permissions=[],
    )
    db = AsyncMock()

    with (
        patch(
            "app.modules.auth.service.UserRepository.get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "app.modules.auth.service.PasswordService.verify_password",
            return_value=True,
        ),
        patch(
            (
                "app.modules.auth.service.RBACRepository"
                ".get_user_roles"
            ),
            new=AsyncMock(return_value=[assigned_role]),
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(
                db=db,
                email=user.email,
                password="StrongPass1!",
                role_id=99,
            )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == ("Selected role is not assigned to this user")
