# Visual Project Layout

## Complete Directory Structure

```
tineco-hass/
│
├── 🔧 Configuration Files
│   ├── manifest.json          # Integration metadata
│   ├── hacs.json             # HACS config
│   ├── LICENSE               # MIT License
│   └── .gitignore            # Git ignore
│
├── 📦 Integration Code
│   └── custom_components/tineco/
│       ├── __init__.py           # Main setup
│       ├── config_flow.py        # Configuration UI
│       ├── client.py             # Tineco API wrapper
│       ├── sensor.py             # Status/info sensors
│       ├── switch.py             # Power control
│       ├── binary_sensor.py      # Online status
│       ├── manifest.json         # Integration manifest
│       │
│       └── 🌐 Localization
│           └── strings/
│               ├── en.json       # English
│               └── es.json       # Spanish
│
├── 📚 Documentation
│   ├── README.md                 # Main docs
│   ├── QUICKSTART.md            # 5-min guide
│   ├── INSTALLATION.md          # Full setup
│   ├── DEVELOPMENT.md           # For developers
│   ├── AUTOMATIONS.md           # Example automations
│   ├── HACS_SETUP.md            # HACS submission
│   ├── PROJECT_SUMMARY.md       # Project overview
│   └── SETUP_CHECKLIST.md       # This checklist
│
├── 🔄 CI/CD
│   └── .github/
│       ├── workflows/
│       │   └── validate.yml     # HACS validation
│       └── copilot-instructions.md
│
└── 📄 Root Files
    └── (all markdown and config files listed above)
```

## Entity Layout

```
Tineco IoT Integration
│
├── 📊 Sensors
│   ├── sensor.tineco_device_status
│   │   └── Shows: "online"
│   │
│   ├── sensor.tineco_firmware_version
│   │   └── Shows: "Firmware version info"
│   │
│   ├── sensor.tineco_api_version
│   │   └── Shows: "API version"
│   │
│   └── sensor.tineco_model
│       └── Shows: "Device model"
│
├── 🔌 Switches
│   └── switch.tineco_power
│       └── Toggle: On/Off
│
└── 🔔 Binary Sensors
    └── binary_sensor.tineco_online
        └── Shows: On/Off (online/offline)
```

## Data Flow

```
User Credentials
    ↓
[config_flow.py]
    ↓
Home Assistant
    ↓
[client.py] ←── API Adapter
    ↓
Tineco IoT API
    ↓
Device Query Results
    ↓
[sensor.py / switch.py / binary_sensor.py]
    ↓
Entities (Home Assistant UI)
    ↓
User Dashboard / Automations
```

## Setup Flow

```
1. Install HACS
   ↓
2. Add Custom Repository
   ↓
3. Install Tineco IoT Integration
   ↓
4. Restart Home Assistant
   ↓
5. Create Integration Entry
   ├─ Email
   ├─ Password
   └─ Device Selected
   ↓
6. Entities Created
   ├─ 4 Sensors
   ├─ 1 Switch
   └─ 1 Binary Sensor
   ↓
7. Ready to Use!
   ├─ Create Automations
   ├─ Add to Dashboard
   └─ Control Device
```

## File Dependencies

```
manifest.json
    └─ Declares domain, platforms, requirements
       
__init__.py
    └─ Imports platforms (sensor, switch, binary_sensor)
    └─ Handles setup/unload
    
config_flow.py
    └─ Creates integration entries
    └─ Validates credentials
    
client.py
    └─ Wraps Tineco API
    └─ Provides async methods
    
sensor.py ──┐
switch.py   ├── Import client.py
binary_sensor.py──┘
    └─ Create entities
    └─ Use client for data
```

## Technology Stack

```
Home Assistant Core
    ↓
├─ Platforms (Sensor, Switch, Binary Sensor)
│   └─ Entity Classes
│
├─ Config Flow
│   └─ Validation & UI
│
└─ Integration System
    └─ Config Entries

Python Libraries
    ├─ requests       (HTTP requests)
    ├─ voluptuous     (Config validation)
    └─ json           (Data parsing)

APIs
    └─ Tineco IoT Endpoints
        ├─ REST: Authentication
        ├─ REST: Device List
        └─ IoT: Device Queries & Control
```

## Documentation Roadmap

```
New Users
    ↓
QUICKSTART.md (5 min)
    ↓ Want more details?
INSTALLATION.md (10 min)
    ↓ Ready to automate?
AUTOMATIONS.md (5 min)
    └─ Dashboard setup

Developers
    ↓
DEVELOPMENT.md (15 min)
    ├─ How to extend
    ├─ Adding sensors
    ├─ Adding switches
    └─ API reference
    ↓ Want to contribute?
HACS_SETUP.md
    └─ Submit to official

Reference
    ├─ PROJECT_SUMMARY.md
    ├─ README.md
    └─ SETUP_CHECKLIST.md
```

## Configuration Hierarchy

```
Home Assistant
    └─ Integration: Tineco IoT
        └─ Config Entry
            ├─ email: "user@example.com"
            ├─ password: "••••••••"
            └─ scan_interval: 300 (seconds)
                ↓
            Devices
                ├─ Device 1
                ├─ Device 2
                └─ Device N
                    ↓
                Entities
                    ├─ Sensors
                    ├─ Switches
                    └─ Binary Sensors
```

## Common Tasks at a Glance

| Task | File | Time |
|------|------|------|
| **Install Integration** | INSTALLATION.md | 10 min |
| **Quick Setup** | QUICKSTART.md | 5 min |
| **Create Dashboard** | AUTOMATIONS.md | 5 min |
| **Add New Sensor** | DEVELOPMENT.md | 15 min |
| **Submit to HACS** | HACS_SETUP.md | 30 min |
| **Troubleshoot** | INSTALLATION.md | varies |
| **Understand Code** | DEVELOPMENT.md | 20 min |

## Quality Checklist

```
Integration Components
├─ __init__.py         ✅
├─ config_flow.py      ✅
├─ client.py           ✅
├─ sensor.py           ✅
├─ switch.py           ✅
├─ binary_sensor.py    ✅
└─ manifest.json       ✅

Localization
├─ strings/en.json     ✅
└─ strings/es.json     ✅

Documentation
├─ README.md           ✅
├─ QUICKSTART.md       ✅
├─ INSTALLATION.md     ✅
├─ DEVELOPMENT.md      ✅
├─ AUTOMATIONS.md      ✅
├─ HACS_SETUP.md       ✅
├─ PROJECT_SUMMARY.md  ✅
└─ SETUP_CHECKLIST.md  ✅

Configuration
├─ hacs.json           ✅
├─ LICENSE             ✅
├─ .gitignore          ✅
└─ .github/workflows/  ✅

Total: 26 files created ✅
```

## Next Step Suggestions

```
┌─ For Installation
│  └─ Read: QUICKSTART.md
│
├─ For Development
│  └─ Read: DEVELOPMENT.md
│
└─ For Everything
   └─ Read: PROJECT_SUMMARY.md
```

---

**Start here:** [QUICKSTART.md](QUICKSTART.md)
