from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.modules.users.model import User
from app.modules.users.schema import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.users.service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("")
async def get_users(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.view")
    ),
) -> dict:
    users = await UserService.get_users(
        db=db,
        skip=skip,
        limit=limit,
    )

    serialized_users = [
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
        for user in users
    ]

    return {
        "success": True,
        "message": "Users retrieved successfully",
        "data": serialized_users,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.view")
    ),
) -> dict:
    user = await UserService.get_user(
        db=db,
        user_id=user_id,
    )

    serialized_user = (
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": serialized_user,
    }


@router.post("")
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.create")
    ),
) -> dict:
    user = await UserService.create_user(
        db=db,
        payload=payload,
    )

    serialized_user = (
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message": "User created successfully",
        "data": serialized_user,
    }


@router.patch("/{user_id}")
async def update_user(
    payload: UserUpdateRequest,
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.update")
    ),
) -> dict:
    user = await UserService.update_user(
        db=db,
        user_id=user_id,
        payload=payload,
    )

    serialized_user = (
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message": "User updated successfully",
        "data": serialized_user,
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.delete")
    ),
) -> dict:
    return await UserService.delete_user(
        db=db,
        user_id=user_id,
    )


@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.activate")
    ),
) -> dict:
    user = await UserService.activate_user(
        db=db,
        user_id=user_id,
    )

    serialized_user = (
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message": "User activated successfully",
        "data": serialized_user,
    }

@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int = Path(gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.deactivate")
    ),
) -> dict:
    user = await UserService.deactivate_user(
        db=db,
        user_id=user_id,
    )

    serialized_user = (
        UserResponse.model_validate(user).model_dump(
            mode="json"
        )
    )

    return {
        "success": True,
        "message": "User deactivated successfully",
        "data": serialized_user,
    }