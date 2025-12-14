"""
Application lifespan events.
Handles startup and shutdown operations.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client
motor_client: Optional[AsyncIOMotorClient] = None


async def create_mongodb_collections_and_indexes() -> None:
    """
    Create MongoDB collections with validation schemas and indexes.

    Creates:
    - conversations collection: Immutable raw conversation data
    - conversation_analyses collection: Mutable analysis results
    """
    if motor_client is None:
        logger.warning("MongoDB client is not initialized")
        return

    db = motor_client[settings.MONGODB_DATABASE]

    # ========================================
    # Collection 1: conversations (원본 대화 데이터)
    # ========================================
    try:
        await db.create_collection(
            "conversations",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": [
                        "conversation_id",
                        "child_id",
                        "device_id",
                        "session_id",
                        "messages",
                        "started_at",
                        "created_at",
                    ],
                    "properties": {
                        "conversation_id": {"bsonType": "string"},
                        "child_id": {"bsonType": "string"},
                        "device_id": {"bsonType": "string"},
                        "session_id": {"bsonType": "string"},
                        "messages": {
                            "bsonType": "array",
                            "minItems": 1,
                            "items": {
                                "bsonType": "object",
                                "required": ["message_id", "role", "content", "timestamp"],
                                "properties": {
                                    "message_id": {"bsonType": "string"},
                                    "role": {"enum": ["child", "assistant"]},
                                    "content": {"bsonType": "string"},
                                    "timestamp": {"bsonType": "date"},
                                },
                            },
                        },
                        "started_at": {"bsonType": "date"},
                        "created_at": {"bsonType": "date"},
                    },
                }
            },
        )
        logger.info("Created 'conversations' collection with validation schema")
    except Exception as e:
        logger.info(f"conversations collection already exists: {e}")

    conversations = db.conversations

    # Create indexes for conversations
    await conversations.create_index([("conversation_id", 1)], unique=True)
    await conversations.create_index([("child_id", 1), ("started_at", -1)])
    await conversations.create_index([("device_id", 1), ("session_id", 1)])
    await conversations.create_index([("started_at", -1)])
    await conversations.create_index(
        [("analysis_status.is_analyzed", 1), ("analysis_status.needs_reanalysis", 1)]
    )
    await conversations.create_index([("analysis_status.analysis_version", 1)])

    # TTL index: auto-delete conversations older than 1 year
    await conversations.create_index(
        [("created_at", 1)], expireAfterSeconds=31536000  # 365 days
    )

    logger.info("✅ MongoDB 'conversations' collection and indexes created")

    # ========================================
    # Collection 2: conversation_analyses (분석 결과 데이터)
    # ========================================
    try:
        await db.create_collection(
            "conversation_analyses",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": [
                        "analysis_id",
                        "conversation_id",
                        "child_id",
                        "analysis_metadata",
                        "created_at",
                    ],
                    "properties": {
                        "analysis_id": {"bsonType": "string"},
                        "conversation_id": {"bsonType": "string"},
                        "child_id": {"bsonType": "string"},
                        "analysis_metadata": {
                            "bsonType": "object",
                            "required": ["version", "analyzed_at", "analyzer"],
                            "properties": {
                                "version": {"bsonType": "string"},
                                "analyzed_at": {"bsonType": "date"},
                                "analyzer": {"bsonType": "string"},
                            },
                        },
                        "created_at": {"bsonType": "date"},
                    },
                }
            },
        )
        logger.info("Created 'conversation_analyses' collection with validation schema")
    except Exception as e:
        logger.info(f"conversation_analyses collection already exists: {e}")

    analyses = db.conversation_analyses

    # Create indexes for conversation_analyses
    await analyses.create_index([("analysis_id", 1)], unique=True)
    await analyses.create_index([("conversation_id", 1), ("analysis_metadata.version", -1)])
    await analyses.create_index([("child_id", 1), ("created_at", -1)])
    await analyses.create_index([("analysis_metadata.version", 1)])
    await analyses.create_index([("analysis_metadata.analyzed_at", -1)])

    # Topic and personality searches
    await analyses.create_index([("topics.primary_topics.topic", 1)])
    await analyses.create_index([("personality_insights.traits.trait", 1)])
    await analyses.create_index([("sentiment.overall_mood", 1)])

    # Content safety monitoring
    await analyses.create_index([("content_safety.requires_parent_review", 1)])
    await analyses.create_index([("content_safety.is_safe", 1)])

    # Performance queries
    await analyses.create_index([("interaction_quality.engagement_score", -1)])

    # Compound index for dashboard queries
    await analyses.create_index(
        [("child_id", 1), ("created_at", -1), ("sentiment.overall_mood", 1)]
    )

    # TTL index: auto-delete analyses older than 2 years
    await analyses.create_index(
        [("created_at", 1)], expireAfterSeconds=63072000  # 730 days (keep longer than raw data)
    )

    logger.info("✅ MongoDB 'conversation_analyses' collection and indexes created")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup and shutdown operations.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup operations
    logger.info("🚀 Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.ENVIRONMENT)

    # Initialize database connection pool
    logger.info("Initializing PostgreSQL connection pool...")
    # Database engine is already created in dependencies.py

    # Initialize Redis connection
    logger.info("Initializing Redis connection...")
    # Redis connections are created per-request in dependencies.py

    # Initialize MongoDB connection
    logger.info("Initializing MongoDB connection...")
    global motor_client
    motor_client = AsyncIOMotorClient(str(settings.MONGODB_URL))

    # Create MongoDB collections and indexes
    await create_mongodb_collections_and_indexes()

    # Initialize external integrations
    logger.info("Initializing external integrations...")
    # TODO: Add ElevenLabs client initialization
    # TODO: Add payment gateway initialization

    logger.info("✅ Application startup complete")

    yield

    # Shutdown operations
    logger.info("👋 Shutting down application...")

    # Close PostgreSQL connections
    logger.info("Closing PostgreSQL connections...")
    from app.core.dependencies import engine

    await engine.dispose()

    # Close Redis connections
    logger.info("Closing Redis connections...")
    # Redis connections are closed per-request in dependencies.py

    # Close MongoDB connections
    logger.info("Closing MongoDB connections...")
    global motor_client
    if motor_client:
        motor_client.close()
        motor_client = None

    logger.info("✅ Application shutdown complete")


async def on_startup() -> None:
    """
    Startup event handler.
    Deprecated in favor of lifespan context manager.
    Kept for reference.
    """
    logger.info("Application startup")


async def on_shutdown() -> None:
    """
    Shutdown event handler.
    Deprecated in favor of lifespan context manager.
    Kept for reference.
    """
    logger.info("Application shutdown")
