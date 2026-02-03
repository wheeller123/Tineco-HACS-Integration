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

# Running speed mapping
RUNNING_SPEED_LEVELS = {
    "Soft": 1,
    "Medium": 2,
    "Max": 3,
}

# Cleaning method mapping
CLEANING_METHOD_LEVELS = {
    "Clean water": 0,
    "Detergent": 1,
}

# Suction power mapping (120W or 150W)
SUCTION_POWER_LEVELS = {
    "120W": 1,
    "150W": 2,
}

# MAX power mapping (120W or 150W)
MAX_POWER_LEVELS = {
    "120W": 1,
    "150W": 2,
}

# Spray volume mapping (Mist, Wet, Medium, Rinse, Max)
SPRAY_VOLUME_LEVELS = {
    "Mist": 1,
    "Wet": 2,
    "Medium": 3,
    "Rinse": 4,
    "Max": 5,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select platform from a config entry."""

    # Add all select controls
    selects = [
        TinecoVolumeSelect(config_entry, hass),
        TinecoRunningSpeedSelect(config_entry, hass),
        TinecoCleaningMethodSelect(config_entry, hass),
        TinecoSuctionPowerSelect(config_entry, hass),
        TinecoMaxPowerSelect(config_entry, hass),
        TinecoSprayVolumeSelect(config_entry, hass),
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
                _LOGGER.error("Failed to send volume level command - no result returned")
                
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


class TinecoBaseSelect(SelectEntity):
    """Base class for Tineco select entities."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant, select_type: str,
                 options_dict: dict, command_key: str, icon: str):
        """Initialize the select."""
        self.config_entry = config_entry
        self.hass = hass
        self.select_type = select_type
        self.options_dict = options_dict
        self.command_key = command_key
        self._attr_should_poll = True
        self._attr_options = list(options_dict.keys())
        self._attr_current_option = list(options_dict.keys())[0]
        self._last_command_time = None
        self._attr_icon = icon

        email = config_entry.data.get("email", "")
        self._attr_unique_id = f"{DOMAIN}_{email}_{select_type}"
        self._attr_name = f"Tineco {select_type.replace('_', ' ').title()}"

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
        if option not in self.options_dict:
            _LOGGER.error(f"Invalid {self.select_type}: {option}")
            return

        value = self.options_dict[option]
        _LOGGER.info(f"Setting {self.select_type} to {option} ({self.command_key}={value})")

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
                    _LOGGER.error(f"Failed to login for {self.select_type} command")
                    return

            device_ctx = stored.get("device")
            if not device_ctx:
                devices = await client.async_get_devices()
                if not devices or not client.devices:
                    _LOGGER.error(f"No devices found for {self.select_type} command")
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

            # Send command
            command = {self.command_key: value}
            _LOGGER.info(f"Sending {self.select_type} command to device {device_id}: {command}")
            result = await client.async_control_device(device_id, command, device_sn, device_class)

            if result:
                _LOGGER.info(f"{self.select_type} command sent successfully: {option}, result: {result}")
                self._attr_current_option = option
                self._last_command_time = datetime.now()
                self.async_write_ha_state()
            else:
                _LOGGER.error(f"Failed to send {self.select_type} command - no result returned")

        except Exception as err:
            _LOGGER.error(f"Error sending {self.select_type} command: {err}")

    async def async_update(self):
        """Update select state."""
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
                # Get current value from coordinator data
                info = coordinator.data

                # Check gci or cfp for the command key field
                payload = None
                if isinstance(info, dict):
                    if 'gci' in info and isinstance(info['gci'], dict):
                        payload = info['gci']
                    elif 'cfp' in info and isinstance(info['cfp'], dict):
                        payload = info['cfp']

                if payload and self.command_key in payload:
                    current_value = payload[self.command_key]
                    # Map value to option name
                    for option_name, option_value in self.options_dict.items():
                        if option_value == current_value:
                            self._attr_current_option = option_name
                            break

        except Exception as err:
            _LOGGER.debug(f"Error updating {self.select_type} select: {err}")


class TinecoRunningSpeedSelect(TinecoBaseSelect):
    """Select entity for Tineco running speed control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the running speed select."""
        super().__init__(
            config_entry,
            hass,
            "running_speed",
            RUNNING_SPEED_LEVELS,
            "rs",  # Running Speed command key
            "mdi:speedometer"
        )


class TinecoCleaningMethodSelect(TinecoBaseSelect):
    """Select entity for Tineco cleaning method control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the cleaning method select."""
        super().__init__(
            config_entry,
            hass,
            "cleaning_method",
            CLEANING_METHOD_LEVELS,
            "cm",  # Cleaning Method command key
            "mdi:spray-bottle"
        )


class TinecoSuctionPowerSelect(TinecoBaseSelect):
    """Select entity for Tineco suction power control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the suction power select."""
        super().__init__(
            config_entry,
            hass,
            "suction_power",
            SUCTION_POWER_LEVELS,
            "sp",  # Suction Power command key
            "mdi:vacuum"
        )


class TinecoMaxPowerSelect(TinecoBaseSelect):
    """Select entity for Tineco MAX power control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the MAX power select."""
        super().__init__(
            config_entry,
            hass,
            "max_power",
            MAX_POWER_LEVELS,
            "mp",  # MAX Power command key
            "mdi:flash"
        )


class TinecoSprayVolumeSelect(TinecoBaseSelect):
    """Select entity for Tineco spray volume control."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the spray volume select."""
        super().__init__(
            config_entry,
            hass,
            "spray_volume",
            SPRAY_VOLUME_LEVELS,
            "wp",  # Spray Volume command key (water pressure)
            "mdi:water-percent"
        )


