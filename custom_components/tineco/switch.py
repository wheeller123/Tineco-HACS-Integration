"""Switch platform for Tineco integration."""

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tineco"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch platform from a config entry."""
    
    # No switches currently enabled
    switches = []
    
    async_add_entities(switches)


class TinecoBaseSwitch(SwitchEntity):
    """Base class for Tineco switches."""

    def __init__(self, config_entry: ConfigEntry, switch_type: str, hass: HomeAssistant):
        """Initialize the switch."""
        self.config_entry = config_entry
        self.switch_type = switch_type
        self.hass = hass
        self._attr_should_poll = True
        self._state = False
        
        email = config_entry.data.get("email", "")
        self._attr_unique_id = f"{DOMAIN}_{email}_{switch_type}"
        self._attr_name = f"Tineco {switch_type.replace('_', ' ').title()}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Tineco Device",
            "manufacturer": "Tineco",
            "model": "IoT Device",
        }

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.info(f"Turning on {self.switch_type}")
        # Send control command to device
        await self._send_command(on=True)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.info(f"Turning off {self.switch_type}")
        # Send control command to device
        await self._send_command(on=False)
        self._state = False
        self.async_write_ha_state()

    async def _send_command(self, on: bool):
        """Send command to device - override in subclasses."""
        pass

    async def async_update(self):
        """Update switch state."""
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
                    _LOGGER.debug("Failed to login during update")
                    return

            device_ctx = stored.get("device")
            if not device_ctx:
                devices = await client.async_get_devices()
                if not devices or not client.devices:
                    return
                first = client.devices[0]
                device_ctx = {
                    "id": first.get("did") or first.get("deviceId"),
                    "class": first.get("className", ""),
                    "resource": first.get("resource", ""),
                }
                self.hass.data[DOMAIN][self.config_entry.entry_id]["device"] = device_ctx

            device_id = device_ctx.get("id")
            device_class = device_ctx.get("class", "")
            device_resource = device_ctx.get("resource", "")
            
            # Get device status to determine if on/off
            status = await client.async_query_device_mode(device_id, device_class, device_resource)
            if status:
                # Try to determine power state from device response
                self._state = True  # Default to on if we got data
            
        except Exception as err:
            _LOGGER.debug(f"Error updating switch: {err}")


class TinecoDevicePowerSwitch(TinecoBaseSwitch):
    """Switch for device power control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the power switch."""
        super().__init__(config_entry, "power", hass)
        self._state = True  # Assume device is on by default

    async def _send_command(self, on: bool):
        """Send power command to device."""
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
                    _LOGGER.error("Failed to login for power command")
                    return

            device_ctx = stored.get("device")
            if not device_ctx:
                devices = await client.async_get_devices()
                if not devices or not client.devices:
                    _LOGGER.error("No devices found for power command")
                    return
                first = client.devices[0]
                device_ctx = {
                    "id": first.get("did") or first.get("deviceId"),
                    "class": first.get("className", ""),
                    "resource": first.get("resource", ""),
                }
                self.hass.data[DOMAIN][self.config_entry.entry_id]["device"] = device_ctx

            device_id = device_ctx.get("id")
            
            # Send power command
            command = {"power": 1 if on else 0}
            result = await client.async_control_device(device_id, command)
            
            if result:
                _LOGGER.info(f"Power command sent: {on}")
            else:
                _LOGGER.error("Failed to send power command")
                
        except Exception as err:
            _LOGGER.error(f"Error sending power command: {err}")

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:power" if self._state else "mdi:power-off"
