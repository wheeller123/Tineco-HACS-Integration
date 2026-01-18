# Complete Installation & Setup Guide

## Prerequisites

- Home Assistant 2024.1.0 or later
- HACS installed and configured
- Tineco account with at least one device
- Stable internet connection

## Step 1: Install HACS (if not already installed)

1. Go to Home Assistant
2. **Settings** → **Device & Services** → **Integrations**
3. Click the search icon (⊕)
4. Search for "HACS"
5. Install the HACS integration
6. Restart Home Assistant
7. Reload the page

## Step 2: Add Custom Repository to HACS

1. Open HACS (top navigation menu)
2. Click **Integrations**
3. Click the three-dot menu (⋮) in the top right
4. Select **Custom repositories**
5. Paste repository URL: `https://github.com/yourusername/tineco-hass`
6. Select category: **Integration**
7. Click **Create**

## Step 3: Install Tineco Integration

1. In HACS, click **Integrations**
2. Search for "Tineco IoT"
3. Click on the Tineco IoT result
4. Click **Install**
5. Select version (usually latest)
6. Wait for installation to complete
7. **Restart Home Assistant** (Settings → System → Restart)

## Step 4: Add Integration to Home Assistant

### Method A: Via UI (Recommended)

1. After restart, go to **Settings** → **Devices & Services**
2. Click **Create Integration** (⊕ button)
3. Search for "Tineco IoT"
4. Click on it
5. Enter your credentials:
   - **Email**: Your Tineco account email
   - **Password**: Your Tineco account password
6. Click **Submit**
7. The integration will:
   - Log into your account
   - Discover your devices
   - Create entities automatically

### Method B: Via YAML Configuration

Add to `configuration.yaml`:

```yaml
tineco:
  email: your_email@example.com
  password: your_password
```

Then restart Home Assistant.

## Step 5: Verify Installation

1. Go to **Settings** → **Devices & Services** → **Devices**
2. Search for "Tineco"
3. You should see your Tineco device listed
4. Click on it to see all entities

### Expected Entities

If successfully installed, you'll see:

**Sensors:**
- `sensor.tineco_device_status` - Current device status
- `sensor.tineco_firmware_version` - Firmware version
- `sensor.tineco_api_version` - API version
- `sensor.tineco_model` - Device model

**Switches:**
- `switch.tineco_power` - Power control

**Binary Sensors:**
- `binary_sensor.tineco_online` - Online status

## Step 6: Configure Update Interval (Optional)

1. Go to **Settings** → **Devices & Services** → **Devices**
2. Find "Tineco IoT" integration
3. Click the three-dot menu (⋮)
4. Select **Options**
5. Adjust **Update interval** (default: 300 seconds / 5 minutes)
6. Click **Submit**

## Step 7: Test the Integration

### Test Power Control

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Search for `switch.tineco_power`
3. Click on it
4. Toggle the switch
5. Device should respond (check in Tineco app)

### Check Logs

1. Go to **Settings** → **System** → **Logs**
2. Look for "tineco" entries
3. Should show successful login and device queries

## Troubleshooting

### "Invalid Authentication" Error

**Solutions:**
- Double-check email and password
- Reset your Tineco password in the official app
- Try logging in with the Tineco app first to verify credentials
- Check if 2FA is enabled (not currently supported)

### Entities Not Appearing

**Solutions:**
1. Check integration is loaded:
   - **Settings** → **Devices & Services**
   - Should see "Tineco IoT" listed

2. Restart Home Assistant:
   - **Settings** → **System** → **Restart**

3. Check logs for errors:
   - **Settings** → **System** → **Logs**
   - Search for "tineco"

4. Verify device is online in Tineco app

### "Connection Timeout" Error

**Solutions:**
- Check internet connection
- Verify Tineco API is accessible
- Try restarting Home Assistant
- Check if your ISP blocks the Tineco API domain

### Device Shows as Offline

**Solutions:**
- Verify device is powered on
- Check device is connected to WiFi
- Restart the device
- Check Tineco app to confirm device is accessible
- Increase scan interval to reduce API calls

## Advanced Configuration

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tineco: debug
    tineco: debug
```

Then restart Home Assistant.

### Multiple Devices

The integration supports multiple Tineco devices:

1. For each device, add a separate config entry:
   - **Settings** → **Devices & Services** → **Create Integration**
   - Add same credentials (they'll discover all devices)

2. Or use YAML with multiple entries:

```yaml
# Not currently supported via YAML, use UI instead
```

### Disable Entity

To disable an entity:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find the entity (e.g., `sensor.tineco_api_version`)
3. Click on it
4. Click the toggle to disable

## Updating the Integration

### Via HACS

1. Open HACS
2. Go to **Integrations**
3. Find "Tineco IoT"
4. If update available, click **Update**
5. Select version
6. Click **Update**
7. Restart Home Assistant

### Manually

1. Delete `custom_components/tineco` folder
2. Download latest version from GitHub
3. Extract to `custom_components/tineco`
4. Restart Home Assistant

## Uninstalling

### Via HACS

1. Open HACS
2. Go to **Integrations**
3. Find "Tineco IoT"
4. Click the three-dot menu
5. Select **Uninstall**
6. Restart Home Assistant

### Manually

1. Delete `custom_components/tineco` folder
2. Go to **Settings** → **Devices & Services**
3. Find "Tineco IoT" integration
4. Click three-dot menu
5. Select **Delete**
6. Restart Home Assistant

## Getting Help

### Check Logs First

Always check Home Assistant logs for error messages:
- **Settings** → **System** → **Logs**
- Search for "tineco"

### Common Issues Checklist

- [ ] Valid Tineco credentials
- [ ] Device is online in Tineco app
- [ ] Internet connection is stable
- [ ] Home Assistant is up to date
- [ ] Integration is installed and loaded
- [ ] No 2FA enabled on Tineco account
- [ ] Firewall not blocking Tineco API

### Report Issues

- GitHub Issues: https://github.com/yourusername/tineco-hass/issues
- Include:
  - Home Assistant version
  - Integration version
  - Relevant log entries
  - Device model/type
  - Any error messages

## Support

- Home Assistant Community: https://community.home-assistant.io/
- GitHub Discussions: https://github.com/yourusername/tineco-hass/discussions
- Documentation: See README.md

## Next Steps

Once installed, you can:

1. **Create automations** - See [AUTOMATIONS.md](AUTOMATIONS.md)
2. **Create scripts** - Control device via service calls
3. **Create templates** - Create custom sensors from Tineco data
4. **Create dashboards** - Visualize device status in Lovelace
5. **Integrate with other services** - Telegram, InfluxDB, etc.
