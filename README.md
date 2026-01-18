# Tineco IoT - Home Assistant HACS Integration

Control your Tineco smart devices through Home Assistant using this custom integration.

## Features

- **Device Discovery**: Automatically discovers Tineco devices in your account
- **Sensor Entities**: 
  - Firmware version
  - API version
  - Device model
  - Battery level
  - Vacuum status (idle, in_operation, self_cleaning, etc.)
  - Waste water tank status (clean/full)
  - Fresh water tank status (empty/full)
- **Switch Controls**:
  - Sound on/off (mute/unmute)
- **Select Controls**:
  - Volume level (Low, Medium, High)
- **Binary Sensors**:
  - Online status
  - Charging status
- **Configuration UI**: Easy setup through Home Assistant UI
- **Multi-language Support**: English and Spanish

## Installation

### Via HACS

1. Go to **HACS** → **Integrations**
2. Click the three dots menu → **Custom repositories**
3. Add: `https://github.com/wheeller123/Tineco-HACS-Integration`
4. Category: `Integration`
5. Search for "Tineco IoT"
6. Click **Install**
7. Restart Home Assistant
8. Go to **Settings** → **Devices & Services** → **Add Integration**
9. Search for "Tineco IoT" and configure

### Manual Installation

1. Copy the `custom_components/tineco` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "Tineco IoT" and configure

## Configuration

### Via UI (Recommended)

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Create Integration** (+ button)
3. Search for "Tineco IoT"
4. Enter your Tineco account email and password
5. Click **Submit**

## Usage

Once configured, the integration will create the following entities:

### Sensors
- `sensor.tineco_firmware_version` - Firmware version
- `sensor.tineco_api_version` - API version  
- `sensor.tineco_model` - Device model (e.g., S7 Flashdry)
- `sensor.tineco_battery` - Battery level percentage
- `sensor.tineco_vacuum_status` - Current vacuum status (idle, in_operation, self_cleaning, docked_standby)
- `sensor.waste_water_tank_status` - Waste water tank status (clean/full)
- `sensor.fresh_water_tank_status` - Fresh water tank status (empty/full)

### Switches
- `switch.tineco_sound` - Sound on/off (mute/unmute control)

### Selects
- `select.tineco_volume_level` - Volume level selection (Low, Medium, High)

### Binary Sensors
- `binary_sensor.tineco_online` - Device online status
- `binary_sensor.tineco_charging` - Charging status

### Automation Examples

#### Remind to empty tank after self-cleaning

```yaml
- alias: "Remind to empty tank after self-cleaning"
  trigger:
    - platform: state
      entity_id: sensor.tineco_vacuum_status
      from: "self_cleaning"
      to: "idle"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "Tineco Cleaning Complete"
        message: "Self-cleaning cycle finished. Remember to empty the waste water tank!"
```

#### Notify when fresh water tank is empty

```yaml
- alias: "Notify when fresh water tank is empty"
  trigger:
    - platform: state
      entity_id: sensor.fresh_water_tank_status
      to: "empty"
  action:
    - service: notify.notify
      data:
        message: "Tineco fresh water tank needs refilling"
```

#### Notify when waste water tank is full

```yaml
- alias: "Notify when waste water tank is full"
  trigger:
    - platform: state
      entity_id: sensor.waste_water_tank_status
      to: "full"
  action:
    - service: notify.notify
      data:
        message: "Tineco waste water tank needs emptying"
```

#### Notify when Tineco goes offline

```yaml
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

- Check the scan interval in integration options (default: 60 seconds)
- Verify your device is connected to the internet
- Check Home Assistant logs for errors: `Settings` → `System` → `Logs`

### Water Tank Status Not Accurate

- Ensure the integration has been restarted after installation
- Check that error codes are being reported correctly by the device
- The sensors update based on device-reported error codes (e2=64 for empty fresh water tank)

## API Queries Used

This integration uses the following device queries:

- **GCI** (Get Controller Info) - Battery level, vacuum status, water tank status, error codes
- **GAV** (Get API Version) - Firmware version information
- **GCF** (Get Config File) - Device configuration
- **CFP** (Get Config Point) - Configuration points including status data
- **QueryMode** - Device operating modes

### Key API Fields

- `bp` - Battery percentage (0-100)
- `wm` - Working mode (0=Idle, 2=Charging, 3/4=In Operation, 8=Docked/Standby, 10=Self-cleaning)
- `e1` - Error code 1 (waste water tank issues)
- `e2` - Error code 2 (64 = fresh water tank empty)
- `e3` - Error code 3 (other errors)
- `vs` - Device online status
- `wp` - Water pressure/percentage
- `vl` - Volume level (1=Low, 2=Medium, 3=High)
- `ms` - Mute status (0=unmuted, 1=muted)

## Support

- GitHub Issues: https://github.com/wheeller123/Tineco-HACS-Integration/issues
- Home Assistant Community: https://community.home-assistant.io/

## Credits

Created by Jack Whelan

## Disclaimer

This integration is not affiliated with Tineco. It uses reverse-engineered APIs. Use at your own risk. I developed this specifically for my S7 Flashdry, it may not work with other models but I am happy to try and add others with comminuty support

## License

MIT License - See LICENSE file for details
