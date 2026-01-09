"""
Device service for registration and pairing.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child import Child
from app.models.device import Device
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceRegisterRequest, DevicePairRequest

logger = logging.getLogger(__name__)


@dataclass
class RegisterResult:
    """Device registration result."""

    success: bool
    device: Optional[Device] = None
    device_id: Optional[str] = None
    device_secret: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PairResult:
    """Device pairing result."""

    success: bool
    child_id: Optional[str] = None
    child_name: Optional[str] = None
    paired_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class UnpairResult:
    """Device unpairing result."""

    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class DeviceService:
    """
    Service for device registration and pairing.

    Handles:
    - Device registration with secret generation
    - Device-child pairing via pairing code
    - Device unpairing
    """

    def __init__(
        self,
        db: AsyncSession,
        redis: Optional[Redis] = None,
    ):
        self.db = db
        self.redis = redis
        self.device_repo = DeviceRepository(db)

    async def register(self, request: DeviceRegisterRequest) -> RegisterResult:
        """
        Register a new device.

        Args:
            request: Registration request with serial, type, firmware

        Returns:
            RegisterResult with device_id and secret on success
        """
        # 1. Check if serial number already exists
        if await self.device_repo.exists_by_serial(request.serial_number):
            return RegisterResult(
                success=False,
                error_code="SERIAL_NUMBER_EXISTS",
                error_message="Device with this serial number already registered",
            )

        # 2. Create device with generated secret
        device, device_secret = await self.device_repo.create(
            serial_number=request.serial_number,
            device_type=request.device_type,
            firmware_version=request.firmware_version,
        )

        logger.info(f"Device registered: {device.serial_number}")

        return RegisterResult(
            success=True,
            device_id=str(device.id),
            device_secret=device_secret,
        )

    async def pair(
        self,
        device: Device,
        request: DevicePairRequest,
    ) -> PairResult:
        """
        Pair device with a child using pairing code.

        Args:
            device: Authenticated device
            request: Pairing request with code

        Returns:
            PairResult with child info on success
        """
        # 1. Check if device is already paired
        if device.child_id:
            return PairResult(
                success=False,
                error_code="ALREADY_PAIRED",
                error_message="Device is already paired with a child",
            )

        # 2. Verify pairing code from Redis
        if not self.redis:
            return PairResult(
                success=False,
                error_code="SERVICE_UNAVAILABLE",
                error_message="Pairing service temporarily unavailable",
            )

        child_id_str = await self._verify_pairing_code(request.pairing_code)
        if not child_id_str:
            return PairResult(
                success=False,
                error_code="INVALID_PAIRING_CODE",
                error_message="Pairing code is invalid or expired",
            )

        # 3. Get child and verify exists
        child_id = UUID(child_id_str)
        child = await self._get_child(child_id)
        if not child:
            return PairResult(
                success=False,
                error_code="CHILD_NOT_FOUND",
                error_message="Child not found",
            )

        # 4. Unpair existing device if any
        existing_device = await self.device_repo.get_by_child_id(child_id)
        if existing_device and existing_device.id != device.id:
            await self.device_repo.unpair(existing_device)
            logger.info(f"Unpaired existing device {existing_device.serial_number}")

        # 5. Pair device with child
        device = await self.device_repo.pair_with_child(device, child_id)

        logger.info(
            f"Device {device.serial_number} paired with child {child.name}"
        )

        return PairResult(
            success=True,
            child_id=str(child.id),
            child_name=child.name,
            paired_at=device.paired_at,
        )

    async def unpair(self, device: Device) -> UnpairResult:
        """
        Unpair device from child.

        Args:
            device: Authenticated device

        Returns:
            UnpairResult
        """
        # 1. Check if device is paired
        if not device.child_id:
            return UnpairResult(
                success=False,
                error_code="NOT_PAIRED",
                error_message="Device is not paired with any child",
            )

        # 2. Unpair
        child_id = device.child_id
        await self.device_repo.unpair(device)

        logger.info(f"Device {device.serial_number} unpaired from child {child_id}")

        return UnpairResult(success=True)

    async def _verify_pairing_code(self, code: str) -> Optional[str]:
        """Verify pairing code and return child_id if valid."""
        key = f"pairing_code:{code}"
        child_id = await self.redis.get(key)

        if child_id:
            # Delete code after use (one-time use)
            await self.redis.delete(key)
            # Redis returns bytes, decode to string
            if isinstance(child_id, bytes):
                child_id = child_id.decode("utf-8")
            return child_id

        return None

    async def _get_child(self, child_id: UUID) -> Optional[Child]:
        """Get child by ID."""
        query = select(Child).where(
            Child.id == child_id,
            Child.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_child_with_user(
        self, child_id: UUID, user_id: UUID
    ) -> Optional[Child]:
        """Get child by ID and verify ownership."""
        query = select(Child).where(
            Child.id == child_id,
            Child.user_id == user_id,
            Child.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ===== GraphQL Methods (Parent App) =====

    async def register_and_pair(
        self,
        user_id: UUID,
        serial_number: str,
        device_secret: str,
        device_type: str,
        firmware_version: str,
        child_id: UUID,
    ) -> RegisterResult:
        """
        Register device and pair with child in one operation.

        Called from parent app via GraphQL after BLE connection.

        Args:
            user_id: Parent user ID (from JWT)
            serial_number: Device MAC address
            device_secret: Secret generated by device
            device_type: Device model type
            firmware_version: Firmware version
            child_id: Child to pair with

        Returns:
            RegisterResult with device on success
        """
        # 1. Verify child ownership
        child = await self._get_child_with_user(child_id, user_id)
        if not child:
            return RegisterResult(
                success=False,
                error_code="CHILD_NOT_FOUND",
                error_message="Child not found or not owned by user",
            )

        # 2. Check if serial number already exists
        existing_device = await self.device_repo.get_by_serial_number(serial_number)
        if existing_device:
            # If same device, just update pairing
            if existing_device.device_secret == device_secret:
                # Unpair from previous child if different
                if existing_device.child_id and existing_device.child_id != child_id:
                    await self.device_repo.unpair(existing_device)

                # Unpair existing device from this child
                child_device = await self.device_repo.get_by_child_id(child_id)
                if child_device and child_device.id != existing_device.id:
                    await self.device_repo.unpair(child_device)

                # Pair with new child
                device = await self.device_repo.pair_with_child(existing_device, child_id)

                logger.info(f"Device {serial_number} re-paired with child {child.name}")

                return RegisterResult(
                    success=True,
                    device=device,
                    device_id=str(device.id),
                )
            else:
                return RegisterResult(
                    success=False,
                    error_code="SERIAL_NUMBER_EXISTS",
                    error_message="Device with this serial number already registered",
                )

        # 3. Unpair existing device from child if any
        existing_child_device = await self.device_repo.get_by_child_id(child_id)
        if existing_child_device:
            await self.device_repo.unpair(existing_child_device)
            logger.info(f"Unpaired existing device {existing_child_device.serial_number}")

        # 4. Create new device with provided secret
        device = Device(
            serial_number=serial_number,
            device_secret=device_secret,
            device_type=device_type,
            firmware_version=firmware_version,
            is_active=True,
            connection_status="offline",
            child_id=child_id,
        )
        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)

        # 5. Set pairing
        device = await self.device_repo.pair_with_child(device, child_id)

        logger.info(f"Device {serial_number} registered and paired with child {child.name}")

        return RegisterResult(
            success=True,
            device=device,
            device_id=str(device.id),
        )

    async def unpair_by_id(
        self,
        user_id: UUID,
        device_id: UUID,
    ) -> UnpairResult:
        """
        Unpair device by ID (from parent app).

        Args:
            user_id: Parent user ID (from JWT)
            device_id: Device ID to unpair

        Returns:
            UnpairResult
        """
        # 1. Get device
        device = await self.device_repo.get_by_id(device_id, include_child=True)
        if not device:
            return UnpairResult(
                success=False,
                error_code="DEVICE_NOT_FOUND",
                error_message="Device not found",
            )

        # 2. Check if device is paired
        if not device.child_id:
            return UnpairResult(
                success=False,
                error_code="NOT_PAIRED",
                error_message="Device is not paired with any child",
            )

        # 3. Verify ownership (child belongs to user)
        child = await self._get_child_with_user(device.child_id, user_id)
        if not child:
            return UnpairResult(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Not authorized to unpair this device",
            )

        # 4. Unpair
        await self.device_repo.unpair(device)

        logger.info(f"Device {device.serial_number} unpaired by user {user_id}")

        return UnpairResult(success=True)
