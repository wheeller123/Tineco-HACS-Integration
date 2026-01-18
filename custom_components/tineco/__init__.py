"""Tineco IoT integration for Home Assistant."""

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch", "binary_sensor", "select"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tineco from a config entry."""
    from .client import TinecoDeviceClient

    hass.data.setdefault(DOMAIN, {})

    email = entry.data.get("email")
    password = entry.data.get("password")

    client = TinecoDeviceClient(email, password)
    device_ctx = None

    # Try to authenticate and discover devices
    try:
        logged_in = await client.async_login()
        if not logged_in:
            _LOGGER.warning("Tineco login failed during setup; entities may show Unknown until next update")
        else:
            devices = await client.async_get_devices()
            if devices and client.devices:
                first = client.devices[0]
                device_ctx = {
                    "id": first.get("did") or first.get("deviceId"),
                    "class": first.get("className", ""),
                    "resource": first.get("resource", ""),
                }
    except Exception as err:
        _LOGGER.debug(f"Error initializing Tineco client: {err}")

    # Initialize hass.data structure BEFORE creating coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "email": email,
        "password": password,
        "client": client,
        "device": device_ctx,
    }

    # Create coordinator to fetch device info once per update cycle
    async def async_update_data():
        """Fetch data from API."""
        stored = hass.data[DOMAIN][entry.entry_id]
        stored_client = stored.get("client")
        
        if not stored_client._initialized:
            logged_in = await stored_client.async_login()
            if not logged_in:
                raise UpdateFailed("Failed to login to Tineco API")

        # Get device context
        stored_device = stored.get("device")
        if not stored_device:
            devices = await stored_client.async_get_devices()
            if not devices or not stored_client.devices:
                raise UpdateFailed("No devices found")
            first = stored_client.devices[0]
            stored_device = {
                "id": first.get("did") or first.get("deviceId"),
                "class": first.get("className", ""),
                "resource": first.get("resource", ""),
            }
            stored["device"] = stored_device

        device_id = stored_device.get("id")
        device_class = stored_device.get("class", "")
        device_resource = stored_device.get("resource", "")

        # Fetch device info once for all entities
        info = await stored_client.async_get_device_info(device_id, device_class, device_resource)
        if not info:
            raise UpdateFailed("Failed to get device info")
        return info

    # Get scan interval from options or default to 60s
    scan_interval = entry.options.get("scan_interval", 60)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="tineco",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
