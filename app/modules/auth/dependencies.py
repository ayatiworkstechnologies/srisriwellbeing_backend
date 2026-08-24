from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.token_service import TokenService
from app.modules.users.model import User
from app.modules.users.repository import UserRepository

bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Enter the JWT access token",
    auto_error=False,
)


@dataclass
class AuthContext:
    user: User
    session_id: int


async def get_auth_context(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
) -> AuthContext:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if (
        credentials is not None
        and credentials.scheme.lower() != "bearer"
    ):
        raise unauthorized

    try:
        token = (
            credentials.credentials
            if credentials is not None
            else request.cookies.get("access_token")
        )

        if not token:
            raise unauthorized

        payload = TokenService.decode_token(token)

        if payload.get("token_type") != "access":
            raise unauthorized

        user_id_value = payload.get("sub")
        session_id_value = payload.get("session_id")

        if user_id_value is None or session_id_value is None:
            raise unauthorized

        user_id = int(user_id_value)
        session_id = int(session_id_value)

    except (ValueError, TypeError):
        raise unauthorized

    session = await AuthRepository.get_active_session(
        db=db,
        session_id=session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is expired or revoked",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if session.user_id != user_id:
        raise unauthorized

    user = await UserRepository.get_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise unauthorized

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account status is {user.status}",
        )

    return AuthContext(
        user=user,
        session_id=session_id,
    )


async def get_current_user(
    auth_context: Annotated[
        AuthContext,
        Depends(get_auth_context),
    ],
) -> User:
    return auth_context.user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

CurrentAuthContext = Annotated[
    AuthContext,
    Depends(get_auth_context),
]
