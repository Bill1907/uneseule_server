"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set test environment variables BEFORE importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-elevenlabs-api-key")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "test-voice-id")
os.environ.setdefault("ELEVENLABS_AGENT_ID", "test-agent-id")


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    from unittest.mock import AsyncMock
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    from unittest.mock import AsyncMock
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.incr = AsyncMock()
    redis.ttl = AsyncMock(return_value=-1)
    redis.expire = AsyncMock()
    redis.close = AsyncMock()
    return redis
