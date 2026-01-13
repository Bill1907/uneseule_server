"""
UserProfileService unit tests.

테스트 시나리오:
=== get_or_create_profile ===
1. 정상: 기존 프로필 조회 성공
2. 정상: 신규 프로필 자동 생성

=== update_profile ===
1. 정상: phone 업데이트 성공
2. 실패: 프로필 없음 -> PROFILE_NOT_FOUND
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user_profile import UserProfile
from app.services.user_profile_service import UserProfileResult, UserProfileService


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_profile():
    """Create a sample user profile for testing."""
    profile = MagicMock(spec=UserProfile)
    profile.user_id = uuid.uuid4()
    profile.phone = "010-1234-5678"
    profile.created_at = datetime.now(timezone.utc)
    profile.updated_at = datetime.now(timezone.utc)
    profile.children = []
    profile.subscription = None
    return profile


class TestGetOrCreateProfile:
    """get_or_create_profile 테스트."""

    @pytest.mark.asyncio
    async def test_get_existing_profile(self, mock_db_session, sample_profile):
        """기존 프로필 조회 성공."""
        service = UserProfileService(mock_db_session)

        with patch.object(
            service.profile_repo, "get_or_create", new_callable=AsyncMock
        ) as mock_get_or_create:
            mock_get_or_create.return_value = sample_profile

            result = await service.get_or_create_profile(
                user_id=sample_profile.user_id,
            )

            assert result.success is True
            assert result.profile is not None
            assert result.profile.user_id == sample_profile.user_id

    @pytest.mark.asyncio
    async def test_create_new_profile(self, mock_db_session):
        """신규 프로필 자동 생성."""
        service = UserProfileService(mock_db_session)
        new_user_id = uuid.uuid4()

        new_profile = MagicMock(spec=UserProfile)
        new_profile.user_id = new_user_id
        new_profile.phone = None
        new_profile.children = []
        new_profile.subscription = None

        with patch.object(
            service.profile_repo, "get_or_create", new_callable=AsyncMock
        ) as mock_get_or_create:
            mock_get_or_create.return_value = new_profile

            result = await service.get_or_create_profile(
                user_id=new_user_id,
            )

            assert result.success is True
            assert result.profile.user_id == new_user_id


class TestUpdateProfile:
    """update_profile 테스트."""

    @pytest.mark.asyncio
    async def test_update_phone_success(self, mock_db_session, sample_profile):
        """전화번호 업데이트 성공."""
        service = UserProfileService(mock_db_session)

        with patch.object(
            service.profile_repo, "get_by_user_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_profile

            with patch.object(
                service.profile_repo, "update", new_callable=AsyncMock
            ) as mock_update:
                updated_profile = MagicMock(spec=UserProfile)
                updated_profile.phone = "010-9999-8888"
                mock_update.return_value = updated_profile

                result = await service.update_profile(
                    user_id=sample_profile.user_id,
                    phone="010-9999-8888",
                )

                assert result.success is True
                assert result.profile.phone == "010-9999-8888"

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self, mock_db_session, sample_profile):
        """프로필 없음 실패."""
        service = UserProfileService(mock_db_session)

        with patch.object(
            service.profile_repo, "get_by_user_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.update_profile(
                user_id=sample_profile.user_id,
                phone="010-9999-8888",
            )

            assert result.success is False
            assert result.error_code == "PROFILE_NOT_FOUND"
