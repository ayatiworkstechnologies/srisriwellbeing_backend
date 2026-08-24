from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.api.endpoints.auth import login, register
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


@pytest.mark.asyncio
async def test_register_forwards_authenticated_user_to_service() -> None:
    payload = RegisterRequest(
        full_name="Test User",
        email="test@example.com",
        phone="+919876543210",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
        role_id=2,
    )
    db = AsyncMock()
    current_user = SimpleNamespace(id=1)
    expected = {"success": True}

    with patch.object(
        AuthService,
        "register",
        new=AsyncMock(return_value=expected),
    ) as register_user:
        result = await register(
            payload=payload,
            db=db,
            current_user=current_user,
        )

    assert result == expected
    register_user.assert_awaited_once_with(
        db=db,
        payload=payload,
        current_user=current_user,
    )


@pytest.mark.asyncio
async def test_login_sets_an_http_only_access_cookie() -> None:
    payload = LoginRequest(
        email="test@example.com",
        password="StrongPass1!",
    )
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={},
    )
    response = Response()
    result = {
        "success": True,
        "data": {"access_token": "access-token"},
    }

    with patch.object(
        AuthService,
        "login",
        new=AsyncMock(return_value=result),
    ):
        returned = await login(
            payload=payload,
            request=request,
            response=response,
            db=AsyncMock(),
        )

    assert returned == result
    cookie = response.headers["set-cookie"]
    assert "access_token=access-token" in cookie
    assert "HttpOnly" in cookie


def test_login_allows_role_to_be_selected_or_omitted() -> None:
    default_payload = LoginRequest(
        email="test@example.com",
        password="StrongPass1!",
    )
    assert default_payload.role_id is None

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
            ("app.modules.auth.service.RBACRepository" ".get_user_roles"),
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
    assert exc_info.value.detail == (
        "Selected role is not assigned to this user"
    )
