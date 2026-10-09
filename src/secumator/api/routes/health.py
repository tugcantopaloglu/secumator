from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from secumator.core import settings
from secumator.core.database import get_db
from secumator.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]) -> HealthResponse:
    db_status = "healthy"
    redis_status = "healthy"

    try:
        await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        db_status = "unhealthy"

    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
    except (RedisError, OSError, ValueError):
        redis_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        version=settings.app_version,
        database=db_status,
        redis=redis_status,
    )


@router.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
