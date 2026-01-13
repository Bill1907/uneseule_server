"""
User service unit tests.

테스트 시나리오:
=== update_profile ===
1. 정상: name 업데이트 성공
2. 정상: phone 업데이트 성공
3. 정상: name + phone 동시 업데이트
4. 실패: 유저 없음 -> USER_NOT_FOUND

=== change_password ===
1. 정상: 비밀번호 변경 성공
2. 실패: 현재 비밀번호 불일치 -> INVALID_CURRENT_PASSWORD
3. 실패: 새 비밀번호가 현재와 동일 -> SAME_PASSWORD
4. 실패: 유저 없음 -> USER_NOT_FOUND

=== deactivate_account ===
1. 정상: 계정 비활성화 (soft delete)
2. 실패: 비밀번호 불일치 -> INVALID_PASSWORD
3. 실패: 유저 없음 -> USER_NOT_FOUND
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.services.user_service import UserResult, UserService


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.name = "Test User"
    user.phone = "010-1234-5678"
    user.password_hash = "$2b$12$test_hash"  # bcrypt hash placeholder
    user.is_active = True
    user.email_verified = True
    user.created_at = datetime.now()
    user.updated_at = None
    return user


class TestUpdateProfile:
    """update_profile 테스트."""

    @pytest.mark.asyncio
    async def test_update_name_success(self, mock_db_session, sample_user):
        """이름 업데이트 성공."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch.object(
                service.user_repo, "update", new_callable=AsyncMock
            ) as mock_update:
                updated_user = MagicMock(spec=User)
                updated_user.name = "New Name"
                mock_update.return_value = updated_user

                result = await service.update_profile(
                    user_id=sample_user.id,
                    name="New Name",
                )

                assert result.success is True
                assert result.user.name == "New Name"
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_phone_success(self, mock_db_session, sample_user):
        """전화번호 업데이트 성공."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch.object(
                service.user_repo, "update", new_callable=AsyncMock
            ) as mock_update:
                updated_user = MagicMock(spec=User)
                updated_user.phone = "010-9999-8888"
                mock_update.return_value = updated_user

                result = await service.update_profile(
                    user_id=sample_user.id,
                    phone="010-9999-8888",
                )

                assert result.success is True
                assert result.user.phone == "010-9999-8888"

    @pytest.mark.asyncio
    async def test_update_name_and_phone_success(self, mock_db_session, sample_user):
        """이름과 전화번호 동시 업데이트 성공."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch.object(
                service.user_repo, "update", new_callable=AsyncMock
            ) as mock_update:
                updated_user = MagicMock(spec=User)
                updated_user.name = "New Name"
                updated_user.phone = "010-9999-8888"
                mock_update.return_value = updated_user

                result = await service.update_profile(
                    user_id=sample_user.id,
                    name="New Name",
                    phone="010-9999-8888",
                )

                assert result.success is True
                assert result.user.name == "New Name"
                assert result.user.phone == "010-9999-8888"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_db_session, sample_user):
        """유저 없음 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.update_profile(
                user_id=sample_user.id,
                name="New Name",
            )

            assert result.success is False
            assert result.error_code == "USER_NOT_FOUND"


class TestChangePassword:
    """change_password 테스트."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, mock_db_session, sample_user):
        """비밀번호 변경 성공."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch(
                "app.services.user_service.SecurityUtils.verify_password"
            ) as mock_verify:
                # 첫 번째: 현재 비밀번호 확인 성공
                # 두 번째: 새 비밀번호가 현재와 다름
                mock_verify.side_effect = [True, False]

                with patch(
                    "app.services.user_service.SecurityUtils.hash_password"
                ) as mock_hash:
                    mock_hash.return_value = "$2b$12$new_hash"

                    with patch.object(
                        service.user_repo, "update_password", new_callable=AsyncMock
                    ) as mock_update:
                        mock_update.return_value = sample_user

                        result = await service.change_password(
                            user_id=sample_user.id,
                            current_password="old_password",
                            new_password="new_password",
                        )

                        assert result.success is True
                        mock_hash.assert_called_once_with("new_password")
                        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(self, mock_db_session, sample_user):
        """현재 비밀번호 불일치 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch(
                "app.services.user_service.SecurityUtils.verify_password"
            ) as mock_verify:
                mock_verify.return_value = False

                result = await service.change_password(
                    user_id=sample_user.id,
                    current_password="wrong_password",
                    new_password="new_password",
                )

                assert result.success is False
                assert result.error_code == "INVALID_CURRENT_PASSWORD"

    @pytest.mark.asyncio
    async def test_change_password_same_password(self, mock_db_session, sample_user):
        """새 비밀번호가 현재와 동일 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch(
                "app.services.user_service.SecurityUtils.verify_password"
            ) as mock_verify:
                # 현재 비밀번호 검증 성공, 새 비밀번호도 현재와 동일
                mock_verify.side_effect = [True, True]

                result = await service.change_password(
                    user_id=sample_user.id,
                    current_password="same_password",
                    new_password="same_password",
                )

                assert result.success is False
                assert result.error_code == "SAME_PASSWORD"

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, mock_db_session, sample_user):
        """유저 없음 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.change_password(
                user_id=sample_user.id,
                current_password="old_password",
                new_password="new_password",
            )

            assert result.success is False
            assert result.error_code == "USER_NOT_FOUND"


class TestDeactivateAccount:
    """deactivate_account 테스트."""

    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_db_session, sample_user):
        """계정 비활성화 성공."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch(
                "app.services.user_service.SecurityUtils.verify_password"
            ) as mock_verify:
                mock_verify.return_value = True

                with patch.object(
                    service.user_repo, "deactivate", new_callable=AsyncMock
                ) as mock_deactivate:
                    deactivated_user = MagicMock(spec=User)
                    deactivated_user.is_active = False
                    mock_deactivate.return_value = deactivated_user

                    result = await service.deactivate_account(
                        user_id=sample_user.id,
                        password="correct_password",
                    )

                    assert result.success is True
                    assert result.user.is_active is False
                    mock_deactivate.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_invalid_password(self, mock_db_session, sample_user):
        """비밀번호 불일치 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = sample_user

            with patch(
                "app.services.user_service.SecurityUtils.verify_password"
            ) as mock_verify:
                mock_verify.return_value = False

                result = await service.deactivate_account(
                    user_id=sample_user.id,
                    password="wrong_password",
                )

                assert result.success is False
                assert result.error_code == "INVALID_PASSWORD"

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, mock_db_session, sample_user):
        """유저 없음 실패."""
        service = UserService(mock_db_session)

        with patch.object(
            service.user_repo, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.deactivate_account(
                user_id=sample_user.id,
                password="any_password",
            )

            assert result.success is False
            assert result.error_code == "USER_NOT_FOUND"
