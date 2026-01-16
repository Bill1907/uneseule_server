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
from app.core.security import clerk_auth


@dataclass
class GraphQLContext(BaseContext):
    """
    GraphQL context containing request-specific data.

    Attributes:
        request: FastAPI request object
        db: Async database session
        user_id: Authenticated user ID from Clerk (None if not authenticated)
        user_email: Authenticated user email from Clerk JWT
        user_name: Authenticated user name from Clerk JWT (optional)
    """

    db: AsyncSession = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None


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

    # Extract user info from Clerk JWT token (RS256/JWKS)
    user_id = None
    user_email = None
    user_name = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            payload = await clerk_auth.verify_token(token)
            if payload:
                user_id = clerk_auth.get_user_id_from_payload(payload)
                user_email = clerk_auth.get_user_email_from_payload(payload)
                user_name = clerk_auth.get_user_name_from_payload(payload)
        except Exception:
            # Token verification failed - treat as unauthenticated
            pass

    return GraphQLContext(
        db=db,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
    )
