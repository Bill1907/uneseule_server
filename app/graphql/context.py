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
from app.core.security import security


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

    # Extract user_id from JWT token
    user_id = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        payload = security.decode_token(token)

        if payload and security.verify_token_type(payload, "access"):
            user_id = payload.get("sub")

    return GraphQLContext(
        db=db,
        user_id=user_id,
    )
