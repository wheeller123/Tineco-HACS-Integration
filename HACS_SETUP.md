# HACS Repository Configuration

## hacs.json

This file is required for HACS compatibility:

```json
{
  "name": "Tineco IoT",
  "homeassistant": "2024.1.0",
  "documentation": "https://github.com/yourusername/tineco-hass",
  "issue_tracker": "https://github.com/yourusername/tineco-hass/issues",
  "requirements": ["requests>=2.28.0"]
}
```

## To Submit to HACS Official Repository

1. **Prepare the repository**:
   - Fork or create a new GitHub repository
   - Follow HACS requirements: https://hacs.xyz/docs/publish/integration

2. **Required files**:
   - `custom_components/tineco/manifest.json` ✓
   - `custom_components/tineco/__init__.py` ✓
   - `custom_components/tineco/strings/en.json` ✓
   - `README.md` ✓
   - `LICENSE` file (add this)
   - `.github/workflows/` (optional but recommended)

3. **Testing before submission**:
   - Install in test Home Assistant instance
   - Test all functionality
   - Check logs for errors
   - Validate manifest.json syntax

4. **Submit**:
   - Create GitHub release with version tag
   - Submit to: https://github.com/hacs/default/issues/new

## Repository Structure

```
tineco-hass/
├── custom_components/tineco/
│   ├── __init__.py
│   ├── manifest.json
│   ├── config_flow.py
│   ├── sensor.py
│   ├── switch.py
│   ├── binary_sensor.py
│   └── strings/
│       ├── en.json
│       └── es.json
├── .github/
│   └── workflows/
│       └── validate.yml
├── README.md
├── LICENSE
└── .gitignore
```

## Environment Setup

For development:

1. Create a test Home Assistant environment:
   ```bash
   docker run -it -p 8123:8123 --name homeassistant homeassistant/home-assistant:latest
   ```

2. Mount custom_components:
   ```bash
   docker cp ./custom_components homeassistant:/config/
   ```

3. Restart Home Assistant

4. Test the integration at http://localhost:8123
