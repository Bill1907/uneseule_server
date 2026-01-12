"""
Unit tests for ChildService.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.child_service import ChildService


class TestCreateChild:
    """Test cases for child creation."""

    @pytest.mark.asyncio
    async def test_create_success(self, mock_db_session):
        """Test successful child creation."""
        user_id = uuid4()
        mock_child = MagicMock()
        mock_child.id = uuid4()
        mock_child.name = "테스트"
        mock_child.birth_date = date(2020, 1, 1)
        mock_child.age = 5

        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.create = AsyncMock(return_value=mock_child)

            service = ChildService(mock_db_session)
            result = await service.create_child(
                user_id=user_id,
                name="테스트",
                birth_date=date(2020, 1, 1),
            )

        assert result.success is True
        assert result.child == mock_child
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_create_with_gender(self, mock_db_session):
        """Test child creation with gender."""
        user_id = uuid4()
        mock_child = MagicMock()
        mock_child.id = uuid4()
        mock_child.name = "테스트"
        mock_child.gender = "male"

        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.create = AsyncMock(return_value=mock_child)

            service = ChildService(mock_db_session)
            result = await service.create_child(
                user_id=user_id,
                name="테스트",
                birth_date=date(2020, 1, 1),
                gender="male",
            )

        assert result.success is True
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_future_birthdate(self, mock_db_session):
        """Test creation fails with future birth date."""
        service = ChildService(mock_db_session)
        result = await service.create_child(
            user_id=uuid4(),
            name="테스트",
            birth_date=date.today() + timedelta(days=1),
        )

        assert result.success is False
        assert result.error_code == "INVALID_BIRTH_DATE"
        assert result.child is None


class TestUpdateChild:
    """Test cases for child update."""

    @pytest.mark.asyncio
    async def test_update_success(self, mock_db_session):
        """Test successful child update."""
        user_id = uuid4()
        child_id = uuid4()
        mock_child = MagicMock()
        mock_child.id = child_id
        mock_child.user_id = user_id
        mock_child.name = "새이름"

        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=mock_child)
            mock_repo.update = AsyncMock(return_value=mock_child)

            service = ChildService(mock_db_session)
            result = await service.update_child(
                user_id=user_id,
                child_id=child_id,
                name="새이름",
            )

        assert result.success is True
        assert result.child == mock_child

    @pytest.mark.asyncio
    async def test_update_child_not_found(self, mock_db_session):
        """Test update fails when child not found."""
        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=None)

            service = ChildService(mock_db_session)
            result = await service.update_child(
                user_id=uuid4(),
                child_id=uuid4(),
                name="새이름",
            )

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_wrong_owner(self, mock_db_session):
        """Test update fails when child belongs to different user."""
        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=None)

            service = ChildService(mock_db_session)
            result = await service.update_child(
                user_id=uuid4(),
                child_id=uuid4(),
                name="새이름",
            )

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_future_birthdate(self, mock_db_session):
        """Test update fails with future birth date."""
        user_id = uuid4()
        child_id = uuid4()
        mock_child = MagicMock()
        mock_child.id = child_id

        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=mock_child)

            service = ChildService(mock_db_session)
            result = await service.update_child(
                user_id=user_id,
                child_id=child_id,
                birth_date=date.today() + timedelta(days=1),
            )

        assert result.success is False
        assert result.error_code == "INVALID_BIRTH_DATE"


class TestDeleteChild:
    """Test cases for child deletion."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_db_session):
        """Test successful child deletion (soft delete)."""
        user_id = uuid4()
        child_id = uuid4()
        mock_child = MagicMock()
        mock_child.id = child_id
        mock_child.is_active = False

        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=mock_child)
            mock_repo.soft_delete = AsyncMock(return_value=mock_child)

            service = ChildService(mock_db_session)
            result = await service.delete_child(
                user_id=user_id,
                child_id=child_id,
            )

        assert result.success is True
        mock_repo.soft_delete.assert_called_once_with(mock_child)

    @pytest.mark.asyncio
    async def test_delete_child_not_found(self, mock_db_session):
        """Test delete fails when child not found."""
        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=None)

            service = ChildService(mock_db_session)
            result = await service.delete_child(
                user_id=uuid4(),
                child_id=uuid4(),
            )

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_delete_wrong_owner(self, mock_db_session):
        """Test delete fails when child belongs to different user."""
        with patch("app.services.child_service.ChildRepository") as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id_and_user = AsyncMock(return_value=None)

            service = ChildService(mock_db_session)
            result = await service.delete_child(
                user_id=uuid4(),
                child_id=uuid4(),
            )

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"
