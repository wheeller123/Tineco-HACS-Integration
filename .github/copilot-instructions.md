# Home Assistant Tineco IoT Integration

## Project Overview

This is a HACS-compatible Home Assistant custom integration for controlling Tineco smart devices via their reverse-engineered IoT API.

## Key Technologies

- **Home Assistant**: Home automation platform
- **HACS**: Community app store for Home Assistant
- **Tineco IoT API**: Cloud-based device control
- **Python**: Integration implementation

## Project Structure

```
custom_components/tineco/
├── __init__.py              # Core integration setup
├── manifest.json            # Integration metadata & dependencies
├── config_flow.py          # User configuration UI
├── client.py               # Tineco API client adapter
├── sensor.py               # Sensor platform (status, version, etc.)
├── switch.py               # Switch platform (power control)
├── binary_sensor.py        # Binary sensor platform (online status)
└── strings/
    ├── en.json            # English localization
    └── es.json            # Spanish localization
```

## Core Features

1. **Authentication**: Tineco account login with credential validation
2. **Device Discovery**: Auto-discovers devices in user's account
3. **Sensor Entities**: 
   - Device status, firmware version, API version, model
4. **Switch Entities**:
   - Device power control
5. **Binary Sensors**:
   - Online/offline status
6. **Configuration UI**: User-friendly setup via Home Assistant UI
7. **Localization**: English and Spanish support

## Development Guidelines

### When to Edit Each File

- **__init__.py**: Adding/removing platforms, setup logic
- **config_flow.py**: Changing authentication, UI options
- **client.py**: API client adapter methods
- **sensor.py**: Adding new sensor entities
- **switch.py**: Adding new switch controls
- **binary_sensor.py**: Adding new binary sensor entities
- **manifest.json**: Dependencies, metadata, requirements

### Adding New Entities

1. Create class in appropriate platform file (sensor/switch/binary_sensor)
2. Inherit from base class (TinecoBaseSensor, etc.)
3. Implement required properties
4. Add translation strings in strings/en.json
5. Register in async_setup_entry

### Testing Locally

1. Copy integration to Home Assistant: `cp -r custom_components/tineco ~/.homeassistant/custom_components/`
2. Restart Home Assistant
3. Add via Settings → Integrations
4. Check logs: Settings → System → Logs

## Related Files

- **README.md** - User-facing documentation
- **INSTALLATION.md** - Step-by-step installation guide
- **DEVELOPMENT.md** - Development and extension guide
- **AUTOMATIONS.md** - Example Home Assistant automations
- **HACS_SETUP.md** - HACS repository setup
- **.github/workflows/** - CI/CD validation

## Important Notes

- Integration requires valid Tineco credentials
- Tineco API is reverse-engineered, use at own risk
- Device must be online and connected to WiFi
- Default update interval: 300 seconds (configurable)

## Next Development Priorities

1. Implement actual API polling with client
2. Add device discovery to config flow
3. Implement service calls for device commands
4. Add more entity types (climate, light, fan)
5. Add YAML configuration support
6. Implement refresh/update methods

## Resources

- Home Assistant Dev Docs: https://developers.home-assistant.io/
- HACS Publishing: https://hacs.xyz/docs/publish/integration
- Tineco Client: See parent directory tineco.py
