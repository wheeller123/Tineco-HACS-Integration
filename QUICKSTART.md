# Quick Start Guide

## For Home Assistant Users

### Install in 3 Steps

1. **Install HACS** (if needed)
   - Settings → Device & Services → Create Integration → Search "HACS"

2. **Add Custom Repository**
   - HACS → Integrations → ⋮ Menu → Custom repositories
   - Add: `https://github.com/yourusername/tineco-hass`
   - Category: Integration

3. **Install & Configure**
   - HACS → Integrations → Search "Tineco IoT" → Install
   - Restart Home Assistant
   - Settings → Devices & Services → Create Integration → Tineco IoT
   - Enter Tineco email & password

**Done!** Your devices are now available in Home Assistant.

## For Developers

### Project Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/tineco-hass
cd tineco-hass

# Install dependencies
pip install -r requirements.txt

# Copy to Home Assistant
cp -r custom_components/tineco ~/.homeassistant/custom_components/

# Or use Docker
docker run -v $(pwd)/custom_components:/config/custom_components \
  -p 8123:8123 homeassistant/home-assistant:latest
```

### File Structure Reference

| File | Purpose |
|------|---------|
| `__init__.py` | Integration entry point |
| `manifest.json` | Metadata and dependencies |
| `config_flow.py` | Setup UI and options |
| `client.py` | Tineco API wrapper |
| `sensor.py` | Status/info sensors |
| `switch.py` | Power control |
| `binary_sensor.py` | Online status |
| `strings/*.json` | Translations |

### Common Tasks

**Add a new sensor:**
```python
# In sensor.py
class TinecoNewSensor(TinecoBaseSensor):
    @property
    def state(self):
        return "value"  # From device data
```

**Add a new switch:**
```python
# In switch.py
class TinecoNewSwitch(TinecoBaseSwitch):
    async def async_turn_on(self, **kwargs):
        # Send command to device
        pass
```

**Access Tineco API:**
```python
# In platform file
from custom_components.tineco.client import TinecoDeviceClient

client = TinecoDeviceClient(email, password)
await client.async_login()
info = await client.async_get_controller_info(device_id)
```

### Debugging

**Enable debug logging:**
```yaml
# configuration.yaml
logger:
  logs:
    custom_components.tineco: debug
```

**Check logs:**
- Settings → System → Logs → Search "tineco"

**Test API:**
```python
from custom_components.tineco.client import TinecoDeviceClient

client = TinecoDeviceClient("email@example.com", "password")
await client.async_login()
devices = await client.async_get_devices()
print(devices)
```

## Available Entities

After installation, you'll have:

| Entity | Type | Purpose |
|--------|------|---------|
| `sensor.tineco_device_status` | Sensor | Current status |
| `sensor.tineco_firmware_version` | Sensor | Firmware info |
| `sensor.tineco_api_version` | Sensor | API version |
| `sensor.tineco_model` | Sensor | Device model |
| `switch.tineco_power` | Switch | Power control |
| `binary_sensor.tineco_online` | Binary | Online status |

## Example Automation

```yaml
# Turn on when motion detected
automation:
  - alias: "Tineco with motion"
    trigger:
      platform: state
      entity_id: binary_sensor.motion
      to: "on"
    action:
      service: switch.turn_on
      target:
        entity_id: switch.tineco_power
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid auth" | Check Tineco credentials |
| No entities appear | Restart Home Assistant |
| Device offline | Check WiFi connection |
| Connection timeout | Check internet, firewall |
| Cannot find integration | Clear browser cache |

## Documentation Links

- **Installation**: [INSTALLATION.md](INSTALLATION.md) - Complete setup guide
- **Development**: [DEVELOPMENT.md](DEVELOPMENT.md) - Extension guide
- **Automations**: [AUTOMATIONS.md](AUTOMATIONS.md) - Example automations
- **GitHub**: https://github.com/yourusername/tineco-hass

## Support

- Issues: GitHub Issues
- Questions: Home Assistant Community Forum
- Discussions: GitHub Discussions

## Next Steps

1. ✅ Install the integration
2. ✅ Add your devices
3. 📊 Create a dashboard
4. 🤖 Set up automations
5. 🔧 Customize for your needs

See [AUTOMATIONS.md](AUTOMATIONS.md) for automation examples.
See [DEVELOPMENT.md](DEVELOPMENT.md) for extension options.
