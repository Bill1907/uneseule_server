"""
Main GraphQL schema for Uneseule Backend.
Combines all queries, mutations, and subscriptions.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.graphql.context import GraphQLContext, get_graphql_context
from app.graphql.mutations.device import DeviceMutations


@strawberry.type
class Query:
    """
    Root Query type combining all query resolvers.

    TODO: Inherit from query classes:
    @strawberry.type
    class Query(UserQueries, ChildQueries, ConversationQueries, InsightQueries):
        pass
    """

    @strawberry.field
    def hello(self) -> str:
        """Placeholder query for testing."""
        return "Hello from Uneseule GraphQL API"


@strawberry.type
class Mutation(DeviceMutations):
    """
    Root Mutation type combining all mutation resolvers.
    """

    @strawberry.mutation
    def echo(self, message: str) -> str:
        """Placeholder mutation for testing."""
        return f"Echo: {message}"


# TODO: Uncomment when subscription resolvers are implemented
# @strawberry.type
# class Subscription:
#     """
#     Root Subscription type for real-time updates.
#     """
#     pass


# Create Strawberry schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # subscription=Subscription,  # Uncomment when subscriptions are ready
)


# Create FastAPI GraphQL router
def create_graphql_router() -> GraphQLRouter:
    """
    Create GraphQL router for FastAPI integration.

    Returns:
        Configured GraphQLRouter instance
    """
    return GraphQLRouter(
        schema,
        context_getter=get_graphql_context,
        graphiql=True,  # Enable GraphiQL interface in development
    )
