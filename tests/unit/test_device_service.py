"""
Unit tests for DeviceService.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.device import DevicePairRequest, DeviceRegisterRequest
from app.services.device_service import DeviceService


class TestDeviceRegistration:
    """Test cases for device registration."""

    @pytest.fixture
    def mock_device_repo(self):
        """Create mock device repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def register_request(self):
        """Sample registration request."""
        return DeviceRegisterRequest(
            serial_number="ABC123XYZ",
            device_type="plush_v1",
            firmware_version="1.0.0",
        )

    @pytest.mark.asyncio
    async def test_register_success(self, mock_db_session, register_request):
        """Test successful device registration."""
        device_id = uuid4()
        mock_device = MagicMock()
        mock_device.id = device_id
        mock_device.serial_number = register_request.serial_number

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.exists_by_serial = AsyncMock(return_value=False)
            mock_repo.create = AsyncMock(
                return_value=(mock_device, "generated-secret-123")
            )

            service = DeviceService(mock_db_session)
            result = await service.register(register_request)

        assert result.success is True
        assert result.device_id == str(device_id)
        assert result.device_secret == "generated-secret-123"
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_register_duplicate_serial(self, mock_db_session, register_request):
        """Test registration fails for duplicate serial number."""
        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.exists_by_serial = AsyncMock(return_value=True)

            service = DeviceService(mock_db_session)
            result = await service.register(register_request)

        assert result.success is False
        assert result.error_code == "SERIAL_NUMBER_EXISTS"
        assert result.device_id is None


class TestDevicePairing:
    """Test cases for device pairing."""

    @pytest.fixture
    def mock_device(self):
        """Create mock device."""
        device = MagicMock()
        device.id = uuid4()
        device.serial_number = "ABC123XYZ"
        device.child_id = None
        device.paired_at = None
        return device

    @pytest.fixture
    def mock_child(self):
        """Create mock child."""
        child = MagicMock()
        child.id = uuid4()
        child.name = "테스트 아이"
        child.is_active = True
        return child

    @pytest.fixture
    def pair_request(self):
        """Sample pairing request."""
        return DevicePairRequest(pairing_code="123456")

    @pytest.mark.asyncio
    async def test_pair_success(
        self, mock_db_session, mock_redis_client, mock_device, mock_child, pair_request
    ):
        """Test successful device pairing."""
        child_id_str = str(mock_child.id)
        mock_redis_client.get = AsyncMock(return_value=child_id_str.encode())
        mock_redis_client.delete = AsyncMock()

        paired_device = MagicMock()
        paired_device.child_id = mock_child.id
        paired_device.paired_at = datetime.now(timezone.utc)

        # Mock the result of db.execute for child query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_child)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_child_id = AsyncMock(return_value=None)
            mock_repo.pair_with_child = AsyncMock(return_value=paired_device)

            service = DeviceService(mock_db_session, mock_redis_client)
            result = await service.pair(mock_device, pair_request)

        assert result.success is True
        assert result.child_id == child_id_str
        assert result.child_name == mock_child.name
        assert result.paired_at is not None

    @pytest.mark.asyncio
    async def test_pair_already_paired(
        self, mock_db_session, mock_redis_client, pair_request
    ):
        """Test pairing fails when device is already paired."""
        device = MagicMock()
        device.child_id = uuid4()  # Already paired

        service = DeviceService(mock_db_session, mock_redis_client)
        result = await service.pair(device, pair_request)

        assert result.success is False
        assert result.error_code == "ALREADY_PAIRED"

    @pytest.mark.asyncio
    async def test_pair_invalid_code(
        self, mock_db_session, mock_redis_client, mock_device, pair_request
    ):
        """Test pairing fails with invalid code."""
        mock_redis_client.get = AsyncMock(return_value=None)  # Code not found

        service = DeviceService(mock_db_session, mock_redis_client)
        result = await service.pair(mock_device, pair_request)

        assert result.success is False
        assert result.error_code == "INVALID_PAIRING_CODE"

    @pytest.mark.asyncio
    async def test_pair_no_redis(self, mock_db_session, mock_device, pair_request):
        """Test pairing fails when Redis is unavailable."""
        service = DeviceService(mock_db_session, redis=None)
        result = await service.pair(mock_device, pair_request)

        assert result.success is False
        assert result.error_code == "SERVICE_UNAVAILABLE"


class TestDeviceUnpairing:
    """Test cases for device unpairing."""

    @pytest.mark.asyncio
    async def test_unpair_success(self, mock_db_session):
        """Test successful device unpairing."""
        device = MagicMock()
        device.id = uuid4()
        device.serial_number = "ABC123XYZ"
        device.child_id = uuid4()  # Currently paired

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.unpair = AsyncMock(return_value=device)

            service = DeviceService(mock_db_session)
            result = await service.unpair(device)

        assert result.success is True
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_unpair_not_paired(self, mock_db_session):
        """Test unpairing fails when device is not paired."""
        device = MagicMock()
        device.child_id = None  # Not paired

        service = DeviceService(mock_db_session)
        result = await service.unpair(device)

        assert result.success is False
        assert result.error_code == "NOT_PAIRED"


class TestRegisterAndPair:
    """Test cases for register_and_pair (GraphQL/BLE flow)."""

    @pytest.fixture
    def mock_child(self):
        """Create mock child."""
        child = MagicMock()
        child.id = uuid4()
        child.name = "테스트 아이"
        child.user_id = uuid4()
        child.is_active = True
        return child

    @pytest.mark.asyncio
    async def test_register_and_pair_success(self, mock_db_session, mock_child):
        """Test successful device registration and pairing."""
        user_id = mock_child.user_id
        child_id = mock_child.id

        mock_device = MagicMock()
        mock_device.id = uuid4()
        mock_device.serial_number = "AA:BB:CC:DD:EE:FF"
        mock_device.child_id = child_id
        mock_device.child = mock_child
        mock_device.paired_at = datetime.now(timezone.utc)

        # Mock child query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_child)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_serial_number = AsyncMock(return_value=None)
            mock_repo.get_by_child_id = AsyncMock(return_value=None)
            mock_repo.pair_with_child = AsyncMock(return_value=mock_device)

            service = DeviceService(mock_db_session)
            result = await service.register_and_pair(
                user_id=user_id,
                serial_number="AA:BB:CC:DD:EE:FF",
                device_secret="test-secret",
                device_type="plush_v1",
                firmware_version="1.0.0",
                child_id=child_id,
            )

        assert result.success is True
        assert result.device is not None
        assert result.device_id == str(mock_device.id)

    @pytest.mark.asyncio
    async def test_register_and_pair_child_not_found(self, mock_db_session):
        """Test fails when child not found or not owned by user."""
        user_id = uuid4()
        child_id = uuid4()

        # Mock child query returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.device_service.DeviceRepository"):
            service = DeviceService(mock_db_session)
            result = await service.register_and_pair(
                user_id=user_id,
                serial_number="AA:BB:CC:DD:EE:FF",
                device_secret="test-secret",
                device_type="plush_v1",
                firmware_version="1.0.0",
                child_id=child_id,
            )

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_register_and_pair_duplicate_serial_wrong_secret(
        self, mock_db_session, mock_child
    ):
        """Test fails when serial exists with different secret."""
        user_id = mock_child.user_id
        child_id = mock_child.id

        existing_device = MagicMock()
        existing_device.device_secret = "different-secret"

        # Mock child query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_child)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_serial_number = AsyncMock(return_value=existing_device)

            service = DeviceService(mock_db_session)
            result = await service.register_and_pair(
                user_id=user_id,
                serial_number="AA:BB:CC:DD:EE:FF",
                device_secret="test-secret",
                device_type="plush_v1",
                firmware_version="1.0.0",
                child_id=child_id,
            )

        assert result.success is False
        assert result.error_code == "SERIAL_NUMBER_EXISTS"


class TestUnpairById:
    """Test cases for unpair_by_id (GraphQL flow)."""

    @pytest.fixture
    def mock_child(self):
        """Create mock child."""
        child = MagicMock()
        child.id = uuid4()
        child.user_id = uuid4()
        child.is_active = True
        return child

    @pytest.mark.asyncio
    async def test_unpair_by_id_success(self, mock_db_session, mock_child):
        """Test successful unpair by ID."""
        user_id = mock_child.user_id
        device_id = uuid4()

        mock_device = MagicMock()
        mock_device.id = device_id
        mock_device.serial_number = "AA:BB:CC:DD:EE:FF"
        mock_device.child_id = mock_child.id

        # Mock child query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_child)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_device)
            mock_repo.unpair = AsyncMock(return_value=mock_device)

            service = DeviceService(mock_db_session)
            result = await service.unpair_by_id(
                user_id=user_id,
                device_id=device_id,
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_unpair_by_id_device_not_found(self, mock_db_session):
        """Test fails when device not found."""
        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            service = DeviceService(mock_db_session)
            result = await service.unpair_by_id(
                user_id=uuid4(),
                device_id=uuid4(),
            )

        assert result.success is False
        assert result.error_code == "DEVICE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unpair_by_id_not_paired(self, mock_db_session):
        """Test fails when device is not paired."""
        mock_device = MagicMock()
        mock_device.child_id = None  # Not paired

        with patch(
            "app.services.device_service.DeviceRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_device)

            service = DeviceService(mock_db_session)
            result = await service.unpair_by_id(
                user_id=uuid4(),
                device_id=uuid4(),
            )

        assert result.success is False
        assert result.error_code == "NOT_PAIRED"
