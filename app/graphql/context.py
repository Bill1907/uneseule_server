"""
GraphQL context for request-specific data.
Provides authenticated user and database session to resolvers.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from app.core.dependencies import AsyncSessionLocal
from app.core.security import neon_auth


@dataclass
class GraphQLContext(BaseContext):
    """
    GraphQL context containing request-specific data.

    Attributes:
        request: FastAPI request object
        db: Async database session
        user_id: Authenticated user ID (None if not authenticated)
    """

    db: AsyncSession = None
    user_id: Optional[str] = None


async def get_graphql_context(request: Request) -> GraphQLContext:
    """
    Create GraphQL context from FastAPI request.

    Args:
        request: FastAPI request object

    Returns:
        GraphQLContext instance with user_id and db session
    """
    # Get database session
    db = AsyncSessionLocal()

    # Extract user_id from Neon Auth JWT token (RS256/JWKS)
    user_id = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            payload = await neon_auth.verify_token(token)
            if payload:
                user_id = neon_auth.get_user_id_from_payload(payload)
        except Exception:
            # Token verification failed - treat as unauthenticated
            pass

    return GraphQLContext(
        db=db,
        user_id=user_id,
    )
