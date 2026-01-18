# Tineco IoT - Home Assistant HACS Integration

Control your Tineco smart devices through Home Assistant using this custom integration.

## Features

- **Device Discovery**: Automatically discovers Tineco devices in your account
- **Sensor Entities**: 
  - Device status
  - Firmware version
  - API version
  - Device model
- **Switch Entities**:
  - Power control (turn device on/off)
- **Binary Sensors**:
  - Online status
- **Configuration UI**: Easy setup through Home Assistant UI
- **Multi-language Support**: English and Spanish

## Installation

### Via HACS

1. Go to **HACS** → **Integrations**
2. Click the three dots menu → **Custom repositories**
3. Add: `https://github.com/yourusername/tineco-hass`
4. Category: `Integration`
5. Search for "Tineco IoT"
6. Click **Install**
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **Create Automation**
9. Search for "Tineco IoT" and configure

### Manual Installation

1. Copy the `custom_components/tineco` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Create Automation**
4. Search for "Tineco IoT" and configure

## Configuration

### Via UI (Recommended)

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Create Integration** (+ button)
3. Search for "Tineco IoT"
4. Enter your Tineco account email and password
5. Click **Submit**

### Via YAML (Alternative)

```yaml
tineco:
  email: your_email@example.com
  password: your_password
```

## Usage

Once configured, the integration will create the following entities:

- `sensor.tineco_device_status` - Current device status
- `sensor.tineco_firmware_version` - Firmware version
- `sensor.tineco_api_version` - API version
- `sensor.tineco_model` - Device model
- `switch.tineco_power` - Device power control
- `binary_sensor.tineco_online` - Device online status

### Automations Example

```yaml
- alias: "Turn off Tineco when away"
  trigger:
    - platform: state
      entity_id: group.all_people
      to: "not_home"
  action:
    - service: switch.turn_off
      entity_id: switch.tineco_power

- alias: "Notify when Tineco goes offline"
  trigger:
    - platform: state
      entity_id: binary_sensor.tineco_online
      to: "off"
  action:
    - service: notify.notify
      data:
        message: "Your Tineco device is offline"
```

## Troubleshooting

### Invalid Authentication Error

- Double-check your email and password
- Ensure your Tineco account is active
- Try resetting your Tineco password on the official app

### Device Not Discovered

- Ensure your device is online
- Check your internet connection
- Restart Home Assistant
- Try removing and re-adding the integration

### Sensors Not Updating

- Check the scan interval (default: 300 seconds)
- Verify your device is connected to the internet
- Check Home Assistant logs for errors: `Settings` → `System` → `Logs`

## Advanced Configuration

### Adjust Update Interval

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Find "Tineco IoT" integration
3. Click the three dots menu
4. Select **Options**
5. Adjust "Update interval" (60-3600 seconds)

## API Queries Used

This integration uses the following device queries:

- **GCI** (Get Controller Info) - Firmware version, hardware info
- **GAV** (Get API Version) - Device API version
- **GCF** (Get Config File) - Device configuration
- **CFP** (Get Config Point) - Configuration points
- **QueryMode** - Device operating modes

## Support

- GitHub Issues: https://github.com/yourusername/tineco-hass/issues
- Home Assistant Community: https://community.home-assistant.io/

## Disclaimer

This integration is not affiliated with Tineco. It uses reverse-engineered APIs. Use at your own risk.

## License

MIT License - See LICENSE file for details
