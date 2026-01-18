"""Binary sensor platform for Tineco integration."""

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up binary sensor platform from a config entry."""
    
    sensors = [
        TinecoDeviceOnlineSensor(config_entry, hass),
        TinecoChargingSensor(config_entry, hass),
    ]
    
    async_add_entities(sensors)


class TinecoBaseBinarySensor(BinarySensorEntity):
    """Base class for Tineco binary sensors."""

    def __init__(self, config_entry: ConfigEntry, sensor_type: str, hass: HomeAssistant):
        """Initialize the binary sensor."""
        self.config_entry = config_entry
        self.sensor_type = sensor_type
        self.hass = hass
        self._attr_should_poll = True
        self._state = True
        self._fail_count = 0
        self._max_fail_before_offline = 3
        
        email = config_entry.data.get("email", "")
        self._attr_unique_id = f"{DOMAIN}_{email}_{sensor_type}"
        self._attr_name = f"Tineco {sensor_type.replace('_', ' ').title()}"

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Tineco Device",
            "manufacturer": "Jack Whelan",
            "model": "IoT Device",
        }

    async def async_update(self):
        """Update binary sensor state."""
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
                    self._fail_count += 1
                    if self._fail_count >= self._max_fail_before_offline:
                        self._state = False
                    return

            device_ctx = stored.get("device")
            if not device_ctx:
                devices = await client.async_get_devices()
                if not devices or not client.devices:
                    _LOGGER.debug("No devices found")
                    self._fail_count += 1
                    if self._fail_count >= self._max_fail_before_offline:
                        self._state = False
                    return
                first = client.devices[0]
                device_ctx = {
                    "id": first.get("did") or first.get("deviceId"),
                    "class": first.get("className", ""),
                    "resource": first.get("resource", ""),
                }
                self.hass.data[DOMAIN][self.config_entry.entry_id]["device"] = device_ctx

            # Try a lightweight query to confirm online state
            device_id = device_ctx.get("id")
            device_class = device_ctx.get("class", "")
            device_resource = device_ctx.get("resource", "")
            status = await client.async_query_device_mode(device_id, device_class, device_resource)
            if status:
                self._state = True
                self._fail_count = 0
            else:
                self._fail_count += 1
                if self._fail_count >= self._max_fail_before_offline:
                    self._state = False
            
        except Exception as err:
            _LOGGER.debug(f"Error updating binary sensor: {err}")
            self._fail_count += 1
            if self._fail_count >= self._max_fail_before_offline:
                self._state = False


class TinecoDeviceOnlineSensor(TinecoBaseBinarySensor):
    """Binary sensor for device online status."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the online sensor."""
        super().__init__(config_entry, "online", hass)
        self._state = True  # Assume device is online

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:wifi" if self._state else "mdi:wifi-off"


class TinecoChargingSensor(TinecoBaseBinarySensor):
    """Binary sensor for charging state."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the charging sensor."""
        super().__init__(config_entry, "charging", hass)
        self._state = False
        self._unknown_log_count = 0

    async def async_update(self):
        """Update charging state from device query."""
        try:
            stored = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            coordinator = stored.get("coordinator")
            client = stored.get("client")

            # Prefer already-fetched coordinator data; fall back to a fresh query
            payload_candidates = []
            if coordinator and getattr(coordinator, "data", None):
                payload_candidates.extend(self._extract_payloads(coordinator.data))

            if not payload_candidates:
                if client is None:
                    from .client import TinecoDeviceClient
                    email = self.config_entry.data.get("email")
                    password = self.config_entry.data.get("password")
                    client = TinecoDeviceClient(email, password)
                    self.hass.data[DOMAIN][self.config_entry.entry_id]["client"] = client
                    if not await client.async_login():
                        _LOGGER.debug("Failed to login during charging update")
                        return

                device_ctx = stored.get("device")
                if not device_ctx:
                    devices = await client.async_get_devices()
                    if not devices or not client.devices:
                        _LOGGER.debug("No devices found")
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
                status = await client.async_query_device_mode(device_id, device_class, device_resource)
                if isinstance(status, dict):
                    payload_candidates.append(status.get("payload") or status.get("data") or status)

            self._state = any(self._is_charging_from_payload(payload) for payload in payload_candidates)

            if not self._state and payload_candidates and self._unknown_log_count < 3:
                sample = payload_candidates[0] if isinstance(payload_candidates[0], dict) else None
                keys = list(sample.keys()) if isinstance(sample, dict) else "non-dict"
                _LOGGER.debug("Charging not detected; payload keys=%s", keys)
                self._unknown_log_count += 1
        except Exception as err:
            _LOGGER.debug(f"Error updating charging sensor: {err}")

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:battery-charging" if self._state else "mdi:battery"

    def _extract_payloads(self, info):
        """Collect possible payload blobs from coordinator/device info."""
        payloads = []
        if isinstance(info, dict):
            for key in ("query_mode", "gci", "gcf", "cfp"):
                part = info.get(key)
                if isinstance(part, dict):
                    payloads.append(part.get("payload") or part.get("data") or part)
            # Fallback: use the whole info blob if nothing else
            if not payloads:
                payloads.append(info)
        return payloads

    def _is_charging_from_payload(self, payload) -> bool:
        """Infer charging state from known and heuristic fields.
        
        Based on reverse-engineered Tineco Android app (MQTT CFT topic payload):
        - wm (work mode) = 2 indicates charging state
        - bp (battery percentage) > 100 indicates charging (e.g., 238, 239, 240)
        
        See: CHARGING_INDICATOR_ANALYSIS.md from decompiled APK
        """
        if not isinstance(payload, (dict, list, tuple)):
            return False
        
        # Define explicit charging-related keys
        explicit_keys = {
            "charging",
            "ischarging",
            "chargestate",
            "charge_status",
            "charge_status_code",
            "charging_state",
            "is_charging",
            "is_charger",
            "dock",
            "docked",
            "isdocked",
            "plug",
            "plugged",
            "pluggedin",
            "plug_status",
        }

        charge_strings = {"charge", "charging", "recharge", "plug", "dock"}
        charge_values = {"charge", "charging", "recharging", "plugged", "plug", "plug-in", "dock", "docked", "on", "true", "yes", "1"}

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield k, v
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)

        for key, val in walk(payload):
            key_lower = key.lower() if isinstance(key, str) else ""

            # PRIORITY 1: Check Tineco-specific wm (work mode) field
            # wm=2 definitively indicates charging state (from decompiled app)
            if key_lower == "wm":
                try:
                    work_mode = int(val)
                    if work_mode == 2:
                        return True
                except (ValueError, TypeError):
                    pass

            # PRIORITY 2: Battery raw value heuristic
            # Tineco reports >100 (e.g., 238, 239, 240) while docked/charging
            if key_lower in ("bp", "battery", "batterypercent", "battery_percent", "powerpercent", "elec", "electricquantity", "battery_level", "soc"):
                try:
                    numeric_val = float(str(val).replace("%", ""))
                    if numeric_val > 100:
                        return True
                except Exception:
                    pass

            # PRIORITY 3: Explicit keys or keys containing charge/dock/plug
            if key_lower in explicit_keys or any(term in key_lower for term in charge_strings):
                if isinstance(val, bool):
                    if val:
                        return True
                elif isinstance(val, str):
                    lower = val.lower()
                    if "discharge" in lower:
                        continue
                    if lower in charge_values or any(term in lower for term in charge_strings):
                        return True
                elif isinstance(val, (int, float)):
                    if val > 0:
                        return True

            # PRIORITY 4: Status-style fields where a specific value indicates charging
            if key_lower in ("status", "state", "workstatus", "work_status", "mode"):
                if isinstance(val, str):
                    lower = val.lower()
                    if "charge" in lower and "discharge" not in lower:
                        return True
                    if any(term in lower for term in ("dock", "plug")):
                        return True
                elif isinstance(val, (int, float)) and val in (2, 3, 4, 5, 6, 100):
                    return True

        return False


class TinecoCleanWaterTankSensor(TinecoBaseBinarySensor):
    """Binary sensor for clean water tank warning."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the clean water tank sensor."""
        super().__init__(config_entry, "clean_water_tank", hass)
        self._state = False
        self._attr_device_class = "problem"

    async def async_update(self):
        """Update clean water tank warning state from device query."""
        try:
            stored = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            coordinator = stored.get("coordinator")
            client = stored.get("client")

            # Prefer already-fetched coordinator data; fall back to a fresh query
            payload_candidates = []
            if coordinator and getattr(coordinator, "data", None):
                payload_candidates.extend(self._extract_payloads(coordinator.data))

            if not payload_candidates:
                if client is None:
                    from .client import TinecoDeviceClient
                    email = self.config_entry.data.get("email")
                    password = self.config_entry.data.get("password")
                    client = TinecoDeviceClient(email, password)
                    self.hass.data[DOMAIN][self.config_entry.entry_id]["client"] = client
                    if not await client.async_login():
                        _LOGGER.debug("Failed to login during clean water tank update")
                        return

                device_ctx = stored.get("device")
                if not device_ctx:
                    devices = await client.async_get_devices()
                    if not devices or not client.devices:
                        _LOGGER.debug("No devices found")
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
                status = await client.async_query_device_mode(device_id, device_class, device_resource)
                if isinstance(status, dict):
                    payload_candidates.append(status.get("payload") or status.get("data") or status)

            self._state = any(self._needs_clean_water_from_payload(payload) for payload in payload_candidates)

        except Exception as err:
            _LOGGER.debug(f"Error updating clean water tank sensor: {err}")

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:cup-water" if not self._state else "mdi:cup-off"

    def _extract_payloads(self, info):
        """Collect possible payload blobs from coordinator/device info."""
        payloads = []
        if isinstance(info, dict):
            for key in ("query_mode", "gci", "gcf", "cfp"):
                part = info.get(key)
                if isinstance(part, dict):
                    payloads.append(part.get("payload") or part.get("data") or part)
            # Fallback: use the whole info blob if nothing else
            if not payloads:
                payloads.append(info)
        return payloads

    def _needs_clean_water_from_payload(self, payload) -> bool:
        """Check if clean water tank needs attention.
        
        Checks multiple indicators:
        - e1 error code (clean water tank empty)
        - dv field (device value - 1 might indicate water issue)
        - vs field (vacuum/water status - 0 might indicate low water)
        """
        if not isinstance(payload, (dict, list, tuple)):
            return False

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield k, v
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)

        for key, val in walk(payload):
            key_lower = key.lower() if isinstance(key, str) else ""
            
            # Check e1 error code - indicates clean water tank empty
            if key_lower == "e1" and isinstance(val, (int, float)) and val != 0:
                return True
            
            # Check dv field - might indicate water issue
            if key_lower == "dv" and isinstance(val, (int, float)) and val == 1:
                return True
            
            # Check vs field - 0 might indicate low water
            if key_lower == "vs" and isinstance(val, (int, float)) and val == 0:
                return True

        return False


class TinecoDirtyWaterTankSensor(TinecoBaseBinarySensor):
    """Binary sensor for dirty water tank warning."""

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant):
        """Initialize the dirty water tank sensor."""
        super().__init__(config_entry, "dirty_water_tank", hass)
        self._state = False
        self._attr_device_class = "problem"

    async def async_update(self):
        """Update dirty water tank warning state from device query."""
        try:
            stored = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            coordinator = stored.get("coordinator")
            client = stored.get("client")

            # Prefer already-fetched coordinator data; fall back to a fresh query
            payload_candidates = []
            if coordinator and getattr(coordinator, "data", None):
                payload_candidates.extend(self._extract_payloads(coordinator.data))

            if not payload_candidates:
                if client is None:
                    from .client import TinecoDeviceClient
                    email = self.config_entry.data.get("email")
                    password = self.config_entry.data.get("password")
                    client = TinecoDeviceClient(email, password)
                    self.hass.data[DOMAIN][self.config_entry.entry_id]["client"] = client
                    if not await client.async_login():
                        _LOGGER.debug("Failed to login during dirty water tank update")
                        return

                device_ctx = stored.get("device")
                if not device_ctx:
                    devices = await client.async_get_devices()
                    if not devices or not client.devices:
                        _LOGGER.debug("No devices found")
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
                status = await client.async_query_device_mode(device_id, device_class, device_resource)
                if isinstance(status, dict):
                    payload_candidates.append(status.get("payload") or status.get("data") or status)

            self._state = any(self._needs_empty_dirty_water_from_payload(payload) for payload in payload_candidates)

        except Exception as err:
            _LOGGER.debug(f"Error updating dirty water tank sensor: {err}")

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:water" if not self._state else "mdi:water-alert"

    def _extract_payloads(self, info):
        """Collect possible payload blobs from coordinator/device info."""
        payloads = []
        if isinstance(info, dict):
            for key in ("query_mode", "gci", "gcf", "cfp"):
                part = info.get(key)
                if isinstance(part, dict):
                    payloads.append(part.get("payload") or part.get("data") or part)
            # Fallback: use the whole info blob if nothing else
            if not payloads:
                payloads.append(info)
        return payloads

    def _needs_empty_dirty_water_from_payload(self, payload) -> bool:
        """Check if dirty water tank needs to be emptied.
        
        Based on actual Tineco API testing.
        Checks e2 error code: 64 = dirty water tank full
        """
        if not isinstance(payload, (dict, list, tuple)):
            return False

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield k, v
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    if isinstance(v, (dict, list, tuple)):
                        yield from walk(v)

        for key, val in walk(payload):
            key_lower = key.lower() if isinstance(key, str) else ""
            
            # Check e2 error code - 64 indicates dirty water tank full
            if key_lower == "e2" and isinstance(val, (int, float)) and val == 64:
                return True

        return False
