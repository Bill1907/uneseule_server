"""
FastAPI dependency injection utilities.
Provides common dependencies for database sessions, authentication, etc.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import neon_auth, security

# Database engine and session factory
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency for getting Redis client.

    Yields:
        Redis: Redis async client

    Example:
        @router.get("/cache")
        async def get_cached_data(redis: Redis = Depends(get_redis)):
            ...
    """
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


# HTTP Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """
    Dependency for getting current authenticated user ID from Neon Auth JWT.

    Args:
        credentials: HTTP authorization credentials (Bearer token)

    Returns:
        User ID from Neon Auth token payload

    Raises:
        HTTPException: If token is invalid or missing

    Example:
        @router.get("/me")
        async def get_current_user(
            user_id: str = Depends(get_current_user_id)
        ):
            ...
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = await neon_auth.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = neon_auth.get_user_id_from_payload(payload)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str | None:
    """
    Dependency for optionally getting current user ID from Neon Auth JWT.
    Returns None if no valid token is provided.

    Args:
        credentials: HTTP authorization credentials (Bearer token)

    Returns:
        User ID from token payload or None

    Example:
        @router.get("/public-or-private")
        async def get_data(
            user_id: str | None = Depends(get_current_user_optional)
        ):
            if user_id:
                # Return personalized data
            else:
                # Return public data
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = await neon_auth.verify_token(token)

    if not payload:
        return None

    return neon_auth.get_user_id_from_payload(payload)


# Type aliases for cleaner dependency injection
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
CurrentUserDep = Annotated[str, Depends(get_current_user_id)]
OptionalUserDep = Annotated[str | None, Depends(get_current_user_optional)]
