from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await db.execute(text("SELECT 1"))
        database_status = result.scalar_one()

        return {
            "success": True,
            "message": "Sri Sri Wellbeing API is running",
            "data": {
                "api": "healthy",
                "database": (
                    "connected" if database_status == 1 else "disconnected"
                ),
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from exc
