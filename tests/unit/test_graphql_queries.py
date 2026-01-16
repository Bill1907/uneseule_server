"""
Unit tests for GraphQL query resolvers.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graphql.queries.user import (
    UserQueries,
    _convert_child_to_type,
    _convert_subscription_to_type,
    _convert_profile_to_user_type,
)
from app.graphql.queries.device import DeviceQueries, _convert_device_to_type


class TestConvertProfileToUserType:
    """Tests for _convert_profile_to_user_type function."""

    @pytest.fixture
    def mock_profile(self):
        """Create mock user profile model."""
        profile = MagicMock()
        profile.user_id = "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"
        profile.phone = "010-1234-5678"
        profile.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        profile.updated_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
        profile.children = []
        profile.subscription = None
        return profile

    def test_convert_profile_basic(self, mock_profile):
        """Test basic profile conversion."""
        result = _convert_profile_to_user_type(
            profile=mock_profile,
            email="parent@example.com",
            name="홍길동",
        )

        assert result.id == mock_profile.user_id
        assert result.email == "parent@example.com"
        assert result.name == "홍길동"
        assert result.phone == "010-1234-5678"
        assert result.children == []
        assert result.subscription is None

    def test_convert_profile_with_children(self, mock_profile):
        """Test profile conversion with children."""
        child = MagicMock()
        child.id = uuid.uuid4()
        child.name = "홍아이"
        child.birth_date = date(2020, 5, 15)
        child.gender = "female"
        child.age = 4
        child.is_active = True
        child.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child.updated_at = None
        child.device = None

        mock_profile.children = [child]

        result = _convert_profile_to_user_type(
            profile=mock_profile,
            email="parent@example.com",
        )

        assert len(result.children) == 1
        assert result.children[0].name == "홍아이"
        assert result.children[0].age == 4

    def test_convert_profile_with_subscription(self, mock_profile):
        """Test profile conversion with subscription."""
        subscription = MagicMock()
        subscription.id = uuid.uuid4()
        subscription.plan_type = "premium"
        subscription.status = "active"
        subscription.started_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        subscription.expires_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        subscription.auto_renew = True
        subscription.is_expired = False
        subscription.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        subscription.updated_at = None

        mock_profile.subscription = subscription

        result = _convert_profile_to_user_type(
            profile=mock_profile,
            email="parent@example.com",
        )

        assert result.subscription is not None
        assert result.subscription.plan_type.value == "premium"
        assert result.subscription.auto_renew is True


class TestConvertChildToType:
    """Tests for _convert_child_to_type function."""

    @pytest.fixture
    def mock_child(self):
        """Create mock child model."""
        child = MagicMock()
        child.id = uuid.uuid4()
        child.name = "홍아이"
        child.birth_date = date(2020, 5, 15)
        child.gender = "male"
        child.age = 4
        child.is_active = True
        child.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child.updated_at = None
        child.device = None
        return child

    def test_convert_child_basic(self, mock_child):
        """Test basic child conversion."""
        result = _convert_child_to_type(mock_child)

        assert result.id == str(mock_child.id)
        assert result.name == "홍아이"
        assert result.birth_date == date(2020, 5, 15)
        assert result.gender == "male"
        assert result.age == 4
        assert result.is_active is True
        assert result.device is None

    def test_convert_child_with_device(self, mock_child):
        """Test child conversion with paired device."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "ABC123"
        device.device_type = "bunny_v1"
        device.firmware_version = "1.0.0"
        device.battery_level = 85
        device.connection_status = "online"
        device.is_active = True
        device.paired_at = datetime(2024, 3, 1, tzinfo=timezone.utc)
        device.child_id = mock_child.id
        device.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device.updated_at = None

        mock_child.device = device

        result = _convert_child_to_type(mock_child)

        assert result.device is not None
        assert result.device.serial_number == "ABC123"
        assert result.device.battery_level == 85
        assert result.device.connection_status.value == "online"


class TestConvertDeviceToType:
    """Tests for _convert_device_to_type function."""

    @pytest.fixture
    def mock_device(self):
        """Create mock device model."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "DEV001"
        device.device_type = "bunny_v2"
        device.firmware_version = "2.0.0"
        device.battery_level = 90
        device.connection_status = "online"
        device.is_active = True
        device.paired_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        device.child_id = uuid.uuid4()
        device.child = MagicMock()
        device.child.name = "테스트아이"
        device.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device.updated_at = None
        return device

    def test_convert_device_basic(self, mock_device):
        """Test basic device conversion."""
        result = _convert_device_to_type(mock_device)

        assert result.id == str(mock_device.id)
        assert result.serial_number == "DEV001"
        assert result.device_type == "bunny_v2"
        assert result.firmware_version == "2.0.0"
        assert result.battery_level == 90
        assert result.connection_status.value == "online"
        assert result.child_name == "테스트아이"

    def test_convert_device_without_child(self, mock_device):
        """Test device conversion without paired child."""
        mock_device.child = None
        mock_device.child_id = None

        result = _convert_device_to_type(mock_device)

        assert result.child_id is None
        assert result.child_name is None


class TestUserQueries:
    """Tests for UserQueries resolver class."""

    @pytest.fixture
    def mock_context(self, mock_db_session):
        """Create mock GraphQL context."""
        context = MagicMock()
        context.user_id = "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"
        context.user_email = "test@example.com"
        context.user_name = "테스트"
        context.db = mock_db_session
        return context

    @pytest.fixture
    def mock_info(self, mock_context):
        """Create mock strawberry Info object."""
        info = MagicMock()
        info.context = mock_context
        return info

    @pytest.mark.anyio
    async def test_me_authenticated(self, mock_info, mock_db_session):
        """Test me query with authenticated user."""
        from unittest.mock import AsyncMock
        from app.services.user_profile_service import UserProfileResult

        mock_profile = MagicMock()
        mock_profile.user_id = "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"
        mock_profile.phone = None
        mock_profile.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_profile.updated_at = None
        mock_profile.children = []
        mock_profile.subscription = None

        mock_result = UserProfileResult(success=True, profile=mock_profile)

        with patch("app.graphql.queries.user.UserProfileService") as MockService:
            mock_service_instance = MagicMock()
            mock_service_instance.get_or_create_profile = AsyncMock(return_value=mock_result)
            MockService.return_value = mock_service_instance

            queries = UserQueries()
            result = await queries.me(mock_info)

            assert result is not None
            assert result.email == "test@example.com"
            assert result.name == "테스트"

    @pytest.mark.anyio
    async def test_me_unauthenticated(self, mock_info):
        """Test me query without authentication."""
        mock_info.context.user_id = None
        mock_info.context.user_email = None

        queries = UserQueries()
        result = await queries.me(mock_info)

        assert result is None

    @pytest.mark.anyio
    async def test_my_children(self, mock_info, mock_db_session):
        """Test my_children query."""
        child1 = MagicMock()
        child1.id = uuid.uuid4()
        child1.name = "첫째"
        child1.birth_date = date(2019, 1, 1)
        child1.gender = "male"
        child1.age = 5
        child1.is_active = True
        child1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child1.updated_at = None
        child1.device = None

        child2 = MagicMock()
        child2.id = uuid.uuid4()
        child2.name = "둘째"
        child2.birth_date = date(2021, 6, 1)
        child2.gender = "female"
        child2.age = 3
        child2.is_active = True
        child2.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child2.updated_at = None
        child2.device = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [child1, child2]
        mock_db_session.execute.return_value = mock_result

        queries = UserQueries()
        result = await queries.my_children(mock_info)

        assert len(result) == 2
        assert result[0].name == "첫째"
        assert result[1].name == "둘째"

    @pytest.mark.anyio
    async def test_my_children_unauthenticated(self, mock_info):
        """Test my_children query without authentication."""
        mock_info.context.user_id = None

        queries = UserQueries()
        result = await queries.my_children(mock_info)

        assert result == []

    @pytest.mark.anyio
    async def test_my_subscription(self, mock_info, mock_db_session):
        """Test my_subscription query."""
        mock_sub = MagicMock()
        mock_sub.id = uuid.uuid4()
        mock_sub.plan_type = "basic"
        mock_sub.status = "active"
        mock_sub.started_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_sub.expires_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_sub.auto_renew = False
        mock_sub.is_expired = False
        mock_sub.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_sub.updated_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db_session.execute.return_value = mock_result

        queries = UserQueries()
        result = await queries.my_subscription(mock_info)

        assert result is not None
        assert result.plan_type.value == "basic"
        assert result.is_expired is False


class TestDeviceQueries:
    """Tests for DeviceQueries resolver class."""

    @pytest.fixture
    def mock_context(self, mock_db_session):
        """Create mock GraphQL context."""
        context = MagicMock()
        context.user_id = str(uuid.uuid4())
        context.db = mock_db_session
        return context

    @pytest.fixture
    def mock_info(self, mock_context):
        """Create mock strawberry Info object."""
        info = MagicMock()
        info.context = mock_context
        return info

    @pytest.mark.anyio
    async def test_my_devices(self, mock_info, mock_db_session):
        """Test my_devices query."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "TEST001"
        device.device_type = "bunny_v1"
        device.firmware_version = "1.0.0"
        device.battery_level = 75
        device.connection_status = "online"
        device.is_active = True
        device.paired_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        device.child_id = uuid.uuid4()
        device.child = MagicMock()
        device.child.name = "테스트아이"
        device.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device.updated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [device]
        mock_db_session.execute.return_value = mock_result

        queries = DeviceQueries()
        result = await queries.my_devices(mock_info)

        assert len(result) == 1
        assert result[0].serial_number == "TEST001"
        assert result[0].battery_level == 75

    @pytest.mark.anyio
    async def test_my_devices_unauthenticated(self, mock_info):
        """Test my_devices query without authentication."""
        mock_info.context.user_id = None

        queries = DeviceQueries()
        result = await queries.my_devices(mock_info)

        assert result == []

    @pytest.mark.anyio
    async def test_device_by_id(self, mock_info, mock_db_session):
        """Test device query by ID."""
        device_id = uuid.uuid4()

        device = MagicMock()
        device.id = device_id
        device.serial_number = "SINGLE001"
        device.device_type = "bunny_v2"
        device.firmware_version = "2.0.0"
        device.battery_level = 100
        device.connection_status = "offline"
        device.is_active = True
        device.paired_at = datetime(2024, 3, 1, tzinfo=timezone.utc)
        device.child_id = uuid.uuid4()
        device.child = MagicMock()
        device.child.name = "아이이름"
        device.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device.updated_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = device
        mock_db_session.execute.return_value = mock_result

        queries = DeviceQueries()
        result = await queries.device(mock_info, str(device_id))

        assert result is not None
        assert result.serial_number == "SINGLE001"
        assert result.connection_status.value == "offline"

    @pytest.mark.anyio
    async def test_device_not_found(self, mock_info, mock_db_session):
        """Test device query when device doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        queries = DeviceQueries()
        result = await queries.device(mock_info, str(uuid.uuid4()))

        assert result is None
