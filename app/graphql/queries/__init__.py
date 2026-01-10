"""
GraphQL query resolvers.
"""

from app.graphql.queries.device import DeviceQueries
from app.graphql.queries.user import UserQueries

__all__ = ["UserQueries", "DeviceQueries"]
