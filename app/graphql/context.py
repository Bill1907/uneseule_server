"""
GraphQL context for request-specific data.
Provides authenticated user and database session to resolvers.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.extensions import SchemaExtension
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


class DatabaseSessionExtension(SchemaExtension):
    """
    Schema extension to manage database session lifecycle.

    Ensures database sessions are properly closed after each GraphQL operation,
    preventing connection pool exhaustion (QueuePool limit errors).
    """

    async def on_operation(self):
        """
        Manage database session lifecycle around GraphQL operations.

        Creates session before operation, ensures cleanup after completion.
        """
        # Create session and attach to context
        db = AsyncSessionLocal()
        self.execution_context.context.db = db

        try:
            yield  # Execute the GraphQL operation
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()  # Always return connection to pool


async def get_graphql_context(request: Request) -> GraphQLContext:
    """
    Create GraphQL context from FastAPI request.

    Note: Database session is managed by DatabaseSessionExtension,
    not created here to ensure proper lifecycle management.

    Args:
        request: FastAPI request object

    Returns:
        GraphQLContext instance with user_id (db session added by extension)
    """
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
        db=None,  # Will be set by DatabaseSessionExtension
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
    )
