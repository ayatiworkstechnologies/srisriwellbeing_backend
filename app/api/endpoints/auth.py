from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
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


# ============================================================
# STAFF REGISTRATION
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.manage")
    ),
) -> dict:
    """
    Create a staff user.

    This endpoint is NOT public.

    Only authenticated users with the `users.manage`
    permission can create staff accounts.

    Public patient registration must use:
        /patient-auth/register
    """

    return await AuthService.register(
        db=db,
        payload=payload,
        current_user=current_user,
    )


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Authenticate a staff user and create a session.
    """

    # Use the direct client IP here.
    #
    # If the application is behind Nginx / a trusted reverse
    # proxy, forwarded-header handling should be configured
    # at the deployment/server level.
    ip_address = (
        request.client.host
        if request.client
        else None
    )

    return await AuthService.login(
        db=db,
        email=payload.email,
        password=payload.password,
        role_id=payload.role_id,
        user_agent=request.headers.get(
            "user-agent"
        ),
        ip_address=ip_address,
    )


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/me")
async def get_me(
    current_user: CurrentUser,
) -> dict:
    """
    Return the currently authenticated user's profile.
    """

    return {
        "success": True,
        "message": (
            "Current user retrieved successfully"
        ),
        "data": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "status": current_user.status,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "last_login_at": (
                current_user.last_login_at
            ),
            "created_at": current_user.created_at,
        },
    }


# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post("/refresh")
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate a new access token using a valid refresh token.
    """

    return await AuthService.refresh_token(
        db=db,
        refresh_token=payload.refresh_token,
    )


# ============================================================
# LOGOUT CURRENT SESSION
# ============================================================

@router.post("/logout")
async def logout(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Logout the current session.
    """

    return await AuthService.logout(
        db=db,
        session_id=auth_context.session_id,
    )


# ============================================================
# LOGOUT ALL SESSIONS
# ============================================================

@router.post("/logout-all")
async def logout_all(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Revoke all sessions for the current user.
    """

    return await AuthService.logout_all(
        db=db,
        user_id=auth_context.user.id,
    )


# ============================================================
# USER SESSIONS
# ============================================================

@router.get("/sessions")
async def get_sessions(
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return active sessions belonging to the current user.
    """

    return await AuthService.get_sessions(
        db=db,
        user_id=auth_context.user.id,
        current_session_id=(
            auth_context.session_id
        ),
    )


# ============================================================
# REVOKE SESSION
# ============================================================

@router.delete(
    "/sessions/{session_id}"
)
async def revoke_session(
    session_id: int = Path(gt=0),
    auth_context: CurrentAuthContext = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Revoke one of the current user's sessions.
    """

    return await AuthService.revoke_user_session(
        db=db,
        user_id=auth_context.user.id,
        session_id=session_id,
        current_session_id=(
            auth_context.session_id
        ),
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    auth_context: CurrentAuthContext,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change password for the currently authenticated user.
    """

    return await AuthService.change_password(
        db=db,
        user=auth_context.user,
        current_password=(
            payload.current_password
        ),
        new_password=payload.new_password,
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request a password reset.
    """

    return await AuthService.forgot_password(
        db=db,
        email=payload.email,
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reset password using a valid password-reset token.
    """

    return await AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )


# ============================================================
# ACTIVATE USER ACCOUNT
# ============================================================

@router.patch(
    "/users/{user_id}/activate"
)
async def activate_account(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(
        require_permission("users.manage")
    ),
) -> dict:
    """
    Activate a staff/user account.

    Requires:
        users.manage
    """

    return await AuthService.activate_account(
        db=db,
        user_id=user_id,
    )


# ============================================================
# DEACTIVATE USER ACCOUNT
# ============================================================

@router.patch(
    "/users/{user_id}/deactivate"
)
async def deactivate_account(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(
        require_permission("users.manage")
    ),
) -> dict:
    """
    Deactivate a staff/user account.

    Requires:
        users.manage
    """

    return await AuthService.deactivate_account(
        db=db,
        user_id=user_id,
    )


# ============================================================
# UPDATE CURRENT PROFILE
# ============================================================

@router.patch("/profile")
async def update_profile(
    payload: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
) -> dict:
    """
    Update the currently authenticated user's profile.
    """

    return await AuthService.update_profile(
        db=db,
        current_user=current_user,
        payload=payload,
    )
