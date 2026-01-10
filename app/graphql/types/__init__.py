"""
GraphQL type definitions.
"""

from app.graphql.types.base import (
    AuthPayload,
    BaseNode,
    ConnectionStatus,
    ErrorDetail,
    PaginationInfo,
    PlanType,
    SubscriptionStatus,
    SuccessResponse,
)
from app.graphql.types.child import ChildType
from app.graphql.types.device import DeviceType, RegisterDeviceInput, RegisterDevicePayload, UnpairDevicePayload
from app.graphql.types.subscription import SubscriptionType
from app.graphql.types.user import UserType

__all__ = [
    # Base types
    "BaseNode",
    "PaginationInfo",
    "ErrorDetail",
    "SuccessResponse",
    "AuthPayload",
    # Enums
    "ConnectionStatus",
    "PlanType",
    "SubscriptionStatus",
    # Domain types
    "UserType",
    "ChildType",
    "DeviceType",
    "SubscriptionType",
    # Input/Payload types
    "RegisterDeviceInput",
    "RegisterDevicePayload",
    "UnpairDevicePayload",
]
