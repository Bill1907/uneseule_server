"""
GraphQL context for request-specific data.
Provides authenticated user and database session to resolvers.
"""

from dataclasses import dataclass
from typing import Optional, Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Import User model when implemented
# from app.models.user import User


@dataclass
class GraphQLContext:
    """
    GraphQL context containing request-specific data.

    Attributes:
        request: FastAPI request object
        db: Async database session
        user: Authenticated user (None if not authenticated)
    """

    request: Request
    db: AsyncSession
    user: Optional[Any] = None  # TODO: Change to User when model is implemented


async def get_graphql_context(
    request: Request,
) -> GraphQLContext:
    """
    Create GraphQL context from FastAPI request.

    Args:
        request: FastAPI request object

    Returns:
        GraphQLContext instance with user and db session
    """
    # TODO: Get database session from dependency
    # from app.core.dependencies import get_db
    # db = await get_db()
    db = None  # type: ignore

    # TODO: Extract user from JWT token in Authorization header
    # For now, user is None (unauthenticated)
    user = None

    return GraphQLContext(
        request=request,
        db=db,  # type: ignore
        user=user,
    )
