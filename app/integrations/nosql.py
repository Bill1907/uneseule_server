"""
MongoDB integration using Motor (async MongoDB driver).

This module provides:
- MongoDB client initialization
- Database connection management
- Async collection access
- Connection pooling
"""

from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.core.config import settings


class MongoDBClient:
    """
    MongoDB client singleton for managing database connections.

    Uses Motor (async MongoDB driver) for non-blocking I/O operations.
    Implements connection pooling and automatic retry logic.
    """

    _client: AsyncIOMotorClient | None = None
    _database: AsyncIOMotorDatabase | None = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """
        Get MongoDB client instance (singleton pattern).

        Returns:
            AsyncIOMotorClient: MongoDB async client

        Example:
            client = MongoDBClient.get_client()
            db = client[settings.MONGODB_DATABASE]
        """
        if cls._client is None:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,  # Maximum connections in pool
                minPoolSize=10,  # Minimum connections in pool
                maxIdleTimeMS=45000,  # Close connections idle for 45s
                serverSelectionTimeoutMS=5000,  # 5s timeout for server selection
            )
        return cls._client

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get MongoDB database instance.

        Returns:
            AsyncIOMotorDatabase: MongoDB database

        Example:
            db = MongoDBClient.get_database()
            conversations = db.conversations
        """
        if cls._database is None:
            client = cls.get_client()
            cls._database = client[settings.MONGODB_DATABASE]
        return cls._database

    @classmethod
    async def close(cls) -> None:
        """
        Close MongoDB client connection.
        Should be called during application shutdown.

        Example:
            await MongoDBClient.close()
        """
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._database = None

    @classmethod
    async def ping(cls) -> bool:
        """
        Ping MongoDB server to check connection health.

        Returns:
            bool: True if connection is healthy, False otherwise

        Example:
            is_healthy = await MongoDBClient.ping()
            if not is_healthy:
                logger.error("MongoDB connection failed")
        """
        try:
            client = cls.get_client()
            await client.admin.command("ping")
            return True
        except ConnectionFailure:
            return False


async def get_mongodb() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI dependency for getting MongoDB database instance.

    Yields:
        AsyncIOMotorDatabase: MongoDB database instance

    Example:
        @router.get("/conversations")
        async def get_conversations(
            db: AsyncIOMotorDatabase = Depends(get_mongodb)
        ):
            conversations = await db.conversations.find().to_list(100)
            return conversations
    """
    db = MongoDBClient.get_database()
    try:
        yield db
    finally:
        # Connection pooling handles cleanup, no need to close per-request
        pass


# MongoDB dependency type alias for cleaner type hints
from typing import Annotated

from fastapi import Depends

MongoDBDep = Annotated[AsyncIOMotorDatabase, Depends(get_mongodb)]
