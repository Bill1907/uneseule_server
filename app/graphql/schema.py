"""
Main GraphQL schema for Uneseule Backend.
Combines all queries, mutations, and subscriptions.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.graphql.context import GraphQLContext, get_graphql_context


# TODO: Import query, mutation, and subscription classes when implemented
# from app.graphql.queries.user import UserQueries
# from app.graphql.queries.child import ChildQueries
# from app.graphql.mutations.auth import AuthMutations
# from app.graphql.mutations.user import UserMutations


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
class Mutation:
    """
    Root Mutation type combining all mutation resolvers.

    TODO: Inherit from mutation classes:
    @strawberry.type
    class Mutation(AuthMutations, UserMutations, ChildMutations, SubscriptionMutations):
        pass
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
