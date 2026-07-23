from fastapi import APIRouter, Depends, Request, status,  Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import (
    CurrentAuthContext,
    CurrentUser,
    get_current_user,
)

from app.modules.auth.schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserProfileUpdateRequest,
)

from app.modules.auth.service import AuthService
from app.modules.users.model import User


router = APIRouter()



@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.register(
        db=db,
        payload=payload,
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    else:
        ip_address = None

    return await AuthService.login(
        db=db,
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip_address,
    )


@router.get("/me")
async def get_me(
    current_user: CurrentUser,
) -> dict:
    return {
        "success": True,
        "message": "Current user retrieved successfully",
        "data": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "status": current_user.status,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "last_login_at": current_user.last_login_at,
            "created_at": current_user.created_at,
        },
    }

@router.post("/refresh")
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.refresh_token(
        db=db,
        refresh_token=payload.refresh_token,
    )

@router.post("/logout")
async def logout(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.logout(
        db=db,
        session_id=auth_context.session_id,
    )

@router.post("/logout-all")
async def logout_all(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.logout_all(
        db=db,
        user_id=auth_context.user.id,
    )

@router.get("/sessions")
async def get_sessions(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.get_sessions(
        db=db,
        user_id=auth_context.user.id,
        current_session_id=auth_context.session_id,
    )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.revoke_user_session(
        db=db,
        user_id=auth_context.user.id,
        session_id=session_id,
        current_session_id=auth_context.session_id,
    )

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.change_password(
        db=db,
        user=auth_context.user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.forgot_password(
        db=db,
        email=payload.email,
    )

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )

@router.patch("/users/{user_id}/activate")
async def activate_account(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.activate_account(
        db=db,
        user_id=user_id,
    )

@router.patch("/users/{user_id}/deactivate")
async def deactivate_account(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AuthService.deactivate_account(
        db=db,
        user_id=user_id,
    )

@router.patch("/profile")
async def update_profile(
    payload: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return await AuthService.update_profile(
        db=db,
        current_user=current_user,
        payload=payload,
    )