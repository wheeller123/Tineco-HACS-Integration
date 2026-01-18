"""Select platform for Tineco integration."""

import logging
from datetime import datetime, timedelta
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tineco"

# Volume level mapping
VOLUME_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select platform from a config entry."""
    
    # Add volume level selector
    selects = [
        TinecoVolumeSelect(config_entry, hass),
    ]
    
    async_add_entities(selects)


class TinecoVolumeSelect(SelectEntity):
    """Select entity for Tineco volume level control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the volume select."""
        self.config_entry = config_entry
        self.hass = hass
        self._attr_should_poll = True
        self._attr_options = list(VOLUME_LEVELS.keys())
        self._attr_current_option = "Low"
        self._last_command_time = None
        
        email = config_entry.data.get("email", "")
        self._attr_unique_id = f"{DOMAIN}_{email}_volume_level"
        self._attr_name = "Tineco Volume Level"
        self._attr_icon = "mdi:volume-high"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Tineco Device",
            "manufacturer": "Jack Whelan",
            "model": "IoT Device",
        }

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in VOLUME_LEVELS:
            _LOGGER.error(f"Invalid volume level: {option}")
            return
        
        volume_value = VOLUME_LEVELS[option]
        _LOGGER.info(f"Setting volume level to {option} (vl={volume_value})")
        
        try:
            stored = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            client = stored.get("client")
            if client is None:
                from .client import TinecoDeviceClient
                email = self.config_entry.data.get("email")
                password = self.config_entry.data.get("password")
                client = TinecoDeviceClient(email, password)
                self.hass.data[DOMAIN][self.config_entry.entry_id]["client"] = client
                if not await client.async_login():
                    _LOGGER.error("Failed to login for volume level command")
                    return

            device_ctx = stored.get("device")
            if not device_ctx:
                devices = await client.async_get_devices()
                if not devices or not client.devices:
                    _LOGGER.error("No devices found for volume level command")
                    return
                first = client.devices[0]
                device_ctx = {
                    "id": first.get("did") or first.get("deviceId"),
                    "class": first.get("className", ""),
                    "resource": first.get("resource", ""),
                }
                self.hass.data[DOMAIN][self.config_entry.entry_id]["device"] = device_ctx

            device_id = device_ctx.get("id")
            device_sn = device_ctx.get("resource", "")
            device_class = device_ctx.get("class", "")
            
            # Send volume level command
            command = {"vl": volume_value}
            _LOGGER.info(f"Sending volume level command to device {device_id}: {command}")
            result = await client.async_control_device(device_id, command, device_sn, device_class)
            
            if result:
                _LOGGER.info(f"Volume level command sent successfully: {option}, result: {result}")
                self._attr_current_option = option
                self._last_command_time = datetime.now()
                self.async_write_ha_state()
            else:
                _LOGGER.error(f"Failed to send volume level command - no result returned")
                
        except Exception as err:
            _LOGGER.error(f"Error sending volume level command: {err}")

    async def async_update(self):
        """Update volume level state."""
        try:
            # Skip update if a command was sent recently (within 5 seconds)
            if self._last_command_time:
                time_since_command = datetime.now() - self._last_command_time
                if time_since_command < timedelta(seconds=5):
                    _LOGGER.debug(f"Skipping update - recent command sent {time_since_command.total_seconds():.1f}s ago")
                    return
            
            stored = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            coordinator = stored.get("coordinator")
            
            if coordinator and coordinator.data:
                # Get current volume level from coordinator data
                info = coordinator.data
                
                # Check gci or cfp for vl (volume level) field
                payload = None
                if isinstance(info, dict):
                    if 'gci' in info and isinstance(info['gci'], dict):
                        payload = info['gci']
                    elif 'cfp' in info and isinstance(info['cfp'], dict):
                        payload = info['cfp']
                
                if payload and 'vl' in payload:
                    vl_value = payload['vl']
                    # Map vl value to option name
                    for level_name, level_value in VOLUME_LEVELS.items():
                        if level_value == vl_value:
                            self._attr_current_option = level_name
                            break
                    
        except Exception as err:
            _LOGGER.debug(f"Error updating volume level select: {err}")
