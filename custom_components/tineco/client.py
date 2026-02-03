"""Tineco API client adapter for Home Assistant integration."""

import asyncio
import logging
import functools
from typing import Optional, Dict, List
from .tineco_client_impl import TinecoClient

_LOGGER = logging.getLogger(__name__)


def _run_in_executor(func):
    """Run a sync function in an executor."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    return wrapper


class TinecoDeviceClient:
    """Adapter for Tineco IoT API client."""

    def __init__(self, email: str, password: str, device_id: str = None, region: str = "IE"):
        """Initialize Tineco device client."""
        self.email = email
        self.password = password
        self.device_id = device_id
        self.region = region
        self.client = None
        self.devices: List[Dict] = []
        self._initialized = False
        self._device_cache: Dict = {}

    async def async_login(self) -> bool:
        """Authenticate with Tineco API."""
        try:
            self.client = TinecoClient(device_id=self.device_id, region=self.region)
            # Run blocking I/O in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            success, token, user_id = await loop.run_in_executor(
                None,
                lambda: self.client.login(self.email, self.password, request_code=False)
            )

            if success:
                _LOGGER.info(f"Successfully logged into Tineco API ({self.region}). UID: {user_id}")
                self._initialized = True
                return True
            else:
                _LOGGER.error("Failed to login to Tineco API - invalid credentials")
                return False
        except Exception as err:
            _LOGGER.error(f"Error during login: {err}", exc_info=True)
            return False

    async def async_get_devices(self) -> Optional[List[Dict]]:
        if not self._initialized or not self.client:
            return None
        try:
            loop = asyncio.get_event_loop()
            devices_response = await loop.run_in_executor(None, self.client.get_devices)
            if devices_response:
                self.devices = self.client.device_list
                return self.devices
            return None
        except Exception as err:
            _LOGGER.error(f"Error getting devices: {err}")
            return None

    async def async_get_device_info(self, device_id: str, device_class: str = "", device_resource: str = "") -> Optional[Dict]:
        if not self._initialized or not self.client:
            return None
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self.client.get_complete_device_info(device_id, device_class, device_resource))
            return info if info else None
        except Exception as err:
            _LOGGER.error(f"Error getting device info: {err}")
            return None

    async def async_get_controller_info(self, device_id: str,
                                        device_class: str = "",
                                        device_resource: str = "") -> Optional[Dict]:
        """Get controller info (GCI)."""
        if not self._initialized or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.get_controller_info(device_id, device_class, device_resource)
            )
        except Exception as err:
            _LOGGER.error(f"Error getting controller info: {err}")
            return None

    async def async_get_api_version(self, device_id: str,
                                    device_class: str = "",
                                    device_resource: str = "") -> Optional[Dict]:
        """Get API version (GAV)."""
        if not self._initialized or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.get_api_version(device_id, device_class, device_resource)
            )
        except Exception as err:
            _LOGGER.error(f"Error getting API version: {err}")
            return None

    async def async_get_config_file(self, device_id: str,
                                    device_class: str = "",
                                    device_resource: str = "") -> Optional[Dict]:
        """Get config file (GCF)."""
        if not self._initialized or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.get_config_file(device_id, device_class, device_resource)
            )
        except Exception as err:
            _LOGGER.error(f"Error getting config file: {err}")
            return None

    async def async_query_device_mode(self, device_id: str,
                                      device_class: str = "",
                                      device_resource: str = "") -> Optional[Dict]:
        """Query device mode (QueryMode)."""
        if not self._initialized or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.query_device_mode(device_id, device_class, device_resource)
            )
        except Exception as err:
            _LOGGER.error(f"Error querying device mode: {err}")
            return None

    async def async_control_device(self, device_id: str,
                                   command: Dict,
                                   device_sn: str = "",
                                   device_class: str = "",
                                   action: str = "cfp") -> Optional[Dict]:
        """Send control command to device.
        
        Args:
            device_id: Device ID
            command: Command payload
            device_sn: Device serial number
            device_class: Device class
            action: API action (cfp, UpdateMode, DeleteMode, QueryMode)
        """
        if not self._initialized or not self.client:
            return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.client.control_device(device_id, command, device_sn, device_class, action=action)
            )
        except Exception as err:
            _LOGGER.error(f"Error sending device command: {err}")
            return None
