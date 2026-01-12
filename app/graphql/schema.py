"""
Main GraphQL schema for Uneseule Backend.
Combines all queries, mutations, and subscriptions.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.graphql.context import GraphQLContext, get_graphql_context
from app.graphql.mutations.child import ChildMutations
from app.graphql.mutations.device import DeviceMutations
from app.graphql.queries.device import DeviceQueries
from app.graphql.queries.user import UserQueries


@strawberry.type
class Query(UserQueries, DeviceQueries):
    """
    Root Query type combining all query resolvers.
    """

    @strawberry.field
    def hello(self) -> str:
        """Test query."""
        return "Hello from Uneseule GraphQL API"


@strawberry.type
class Mutation(DeviceMutations, ChildMutations):
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
        path="",
        context_getter=get_graphql_context,
        graphql_ide="graphiql",  # Enable GraphiQL interface
    )
