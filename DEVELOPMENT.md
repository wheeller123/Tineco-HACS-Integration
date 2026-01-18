# Integration Development Guide

## Architecture Overview

```
custom_components/tineco/
├── __init__.py              # Main integration setup
├── manifest.json            # Integration metadata
├── config_flow.py          # Configuration UI
├── client.py               # Tineco API client adapter
├── sensor.py               # Sensor platform entities
├── switch.py               # Switch platform entities
├── binary_sensor.py        # Binary sensor platform entities
└── strings/                # Localization
    ├── en.json            # English strings
    └── es.json            # Spanish strings
```

## Core Components

### __init__.py
- Initializes the integration
- Sets up platforms (sensor, switch, binary_sensor)
- Handles config entry loading/unloading

### config_flow.py
- Handles user authentication
- Validates Tineco credentials
- Manages configuration options (scan interval)

### client.py
- Wraps the TinecoClient from tineco.py
- Provides async methods for Home Assistant
- Handles error logging

### Platform Files
- **sensor.py**: Status, firmware, API version, model
- **switch.py**: Device power control
- **binary_sensor.py**: Online status

## How to Extend

### Adding a New Sensor

1. Edit `custom_components/tineco/sensor.py`:

```python
class TinecoNewSensor(TinecoBaseSensor):
    """Sensor for new device property."""

    @property
    def state(self):
        """Return the state."""
        # Get from device data
        return "value"
    
    @property
    def icon(self):
        """Return the icon."""
        return "mdi:icon-name"
```

2. Add to `async_setup_entry`:

```python
sensors = [
    TinecoDeviceStatusSensor(config_entry, "device_status"),
    TinecoNewSensor(config_entry, "new_property"),  # Add this
]
```

3. Add translation in `strings/en.json`:

```json
"entity": {
  "sensor": {
    "new_property": {
      "name": "New Property"
    }
  }
}
```

### Adding a New Switch

Similar to sensors, extend `TinecoBaseSwitch` in `switch.py`:

```python
class TinecoNewSwitch(TinecoBaseSwitch):
    """Switch for new device control."""

    async def async_turn_on(self, **kwargs):
        # Send command
        pass
```

### Integrating Device Queries

Use the `client.py` adapter methods in your entities:

```python
async def async_update(self):
    """Update sensor state from device."""
    if self.client:
        info = await self.client.async_get_controller_info(
            device_id, device_class, device_resource
        )
        if info:
            # Parse and update self._state
```

## API Client Methods

Available through `TinecoDeviceClient`:

- `async_login()` - Authenticate
- `async_get_devices()` - Get device list
- `async_get_device_info()` - All device queries
- `async_get_controller_info()` - GCI
- `async_get_api_version()` - GAV
- `async_get_config_file()` - GCF
- `async_query_device_mode()` - QueryMode
- `async_control_device()` - Send commands

## Testing

### Local Testing with Home Assistant

1. Copy to Home Assistant config:
   ```bash
   cp -r custom_components/tineco /path/to/homeassistant/config/custom_components/
   ```

2. Restart Home Assistant

3. Add integration through UI

4. Check logs:
   ```
   Settings → System → Logs
   ```

### Test with Docker

```bash
docker run -it -p 8123:8123 \
  -v $(pwd)/custom_components:/config/custom_components \
  homeassistant/home-assistant:latest
```

## Debugging

### Enable Debug Logging

In `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tineco: debug
```

### Common Issues

**Config Flow Not Appearing**:
- Check `manifest.json` has `"config_flow": true`
- Restart Home Assistant completely
- Clear browser cache

**Entities Not Created**:
- Check integration is loaded in Settings
- Verify config entry was created
- Check Home Assistant logs for errors

**Device Query Fails**:
- Verify Tineco credentials are correct
- Check internet connection
- Verify device is online in Tineco app

## Next Steps

1. **Add device discovery**: Implement discovery trigger in `config_flow.py`
2. **Add climate platform**: For temperature-based devices
3. **Add light platform**: For lighting control
4. **Implement polling**: Add update methods to sync device state
5. **Add service calls**: Custom services for device actions

## Resources

- Home Assistant Integration Development: https://developers.home-assistant.io/docs/integration_index
- Platform Documentation: https://developers.home-assistant.io/docs/core/entity
- HACS Publishing: https://hacs.xyz/docs/publish/integration
