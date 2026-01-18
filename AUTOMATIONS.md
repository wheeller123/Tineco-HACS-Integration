# Example Automations for Tineco Integration

## Basic Power Control

### Turn on device when motion detected

```yaml
alias: "Tineco auto-on with motion"
description: "Turn on Tineco device when motion is detected"
trigger:
  platform: state
  entity_id: binary_sensor.motion_sensor
  to: "on"
action:
  service: switch.turn_on
  target:
    entity_id: switch.tineco_power
```

### Turn off device on schedule

```yaml
alias: "Tineco auto-off at night"
description: "Turn off Tineco device at 11 PM"
trigger:
  platform: time
  at: "23:00:00"
action:
  service: switch.turn_off
  target:
    entity_id: switch.tineco_power
```

## Notifications

### Alert when device goes offline

```yaml
alias: "Tineco offline alert"
description: "Send notification when device is offline"
trigger:
  platform: state
  entity_id: binary_sensor.tineco_online
  to: "off"
  for:
    minutes: 5
action:
  service: notify.notify
  data:
    title: "Device Offline"
    message: "Your Tineco device has been offline for 5 minutes"
```

### Daily status report

```yaml
alias: "Tineco daily report"
description: "Send device status report every morning"
trigger:
  platform: time
  at: "08:00:00"
action:
  service: notify.notify
  data:
    title: "Tineco Status Report"
    message: >
      Firmware: {{ state_attr('sensor.tineco_firmware_version', 'value') }}
      Status: {{ states('sensor.tineco_device_status') }}
      Online: {{ states('binary_sensor.tineco_online') }}
```

## Advanced Logic

### Conditional control based on time

```yaml
alias: "Tineco smart schedule"
trigger:
  platform: time_pattern
  minutes: "/30"  # Every 30 minutes
action:
  choose:
    - conditions:
        - condition: time
          after: "08:00:00"
          before: "22:00:00"
      sequence:
        - service: switch.turn_on
          target:
            entity_id: switch.tineco_power
    - default:
        - service: switch.turn_off
          target:
            entity_id: switch.tineco_power
```

### Scene-based control

```yaml
alias: "Tineco scenes"
trigger:
  platform: state
  entity_id: input_select.home_scene
action:
  choose:
    - conditions:
        - condition: state
          entity_id: input_select.home_scene
          state: "Cleaning"
      sequence:
        - service: switch.turn_on
          target:
            entity_id: switch.tineco_power
    - conditions:
        - condition: state
          entity_id: input_select.home_scene
          state: "Away"
      sequence:
        - service: switch.turn_off
          target:
            entity_id: switch.tineco_power
    - conditions:
        - condition: state
          entity_id: input_select.home_scene
          state: "Night"
      sequence:
        - service: switch.turn_off
          target:
            entity_id: switch.tineco_power
```

## Template Sensors

Create custom sensors from Tineco data:

```yaml
template:
  - sensor:
      - name: "Tineco Uptime"
        icon: "mdi:clock"
        unit_of_measurement: "hours"
        state: >
          {% set state = states('sensor.tineco_device_status') %}
          {% if state == 'online' %}
            {{ (now() - states.sensor.tineco_last_online.last_changed).total_seconds() / 3600 | int }}
          {% else %}
            0
          {% endif %}

      - name: "Tineco Status Readable"
        icon: "mdi:information"
        state: >
          {% set status = states('sensor.tineco_device_status') %}
          {% if status == 'online' %} Online
          {% elif status == 'offline' %} Offline
          {% else %} Unknown
          {% endif %}
```

## Conditional Actions

### Only control if certain conditions met

```yaml
alias: "Safe Tineco control"
trigger:
  platform: state
  entity_id: switch.tineco_power
action:
  condition:
    - condition: state
      entity_id: person.user
      state: "home"
    - condition: state
      entity_id: binary_sensor.tineco_online
      state: "on"
  then:
    - service: logbook.log
      data:
        name: "Tineco Action"
        message: "Device control executed"
```

## Integration with Other Services

### Send to Telegram

```yaml
alias: "Tineco status to Telegram"
trigger:
  platform: state
  entity_id: binary_sensor.tineco_online
action:
  service: notify.telegram
  data:
    message: >
      Tineco Status:
      Device: {{ state_attr('sensor.tineco_model', 'value') }}
      Firmware: {{ state_attr('sensor.tineco_firmware_version', 'value') }}
      Online: {{ states('binary_sensor.tineco_online') }}
```

### Log to InfluxDB

```yaml
alias: "Tineco data logging"
trigger:
  platform: time_pattern
  minutes: "/15"  # Every 15 minutes
action:
  service: influxdb.write
  data:
    measurement: "tineco_device"
    tags:
      device: "tineco_main"
    fields:
      online: "{{ states('binary_sensor.tineco_online') == 'on' | int }}"
      power: "{{ states('switch.tineco_power') == 'on' | int }}"
```

## Lovelace Card Examples

### Status Card

```yaml
type: entities
title: Tineco Status
entities:
  - entity: sensor.tineco_device_status
    name: Status
  - entity: binary_sensor.tineco_online
    name: Online
  - entity: sensor.tineco_firmware_version
    name: Firmware
  - entity: sensor.tineco_model
    name: Model
  - entity: switch.tineco_power
    name: Power
```

### Control Panel

```yaml
type: vertical-stack
cards:
  - type: button
    entity: switch.tineco_power
    name: Tineco Power
    icon: mdi:power
    tap_action:
      action: toggle
  - type: conditional
    conditions:
      - entity: binary_sensor.tineco_online
        state: "off"
    card:
      type: markdown
      content: "⚠️ Device is offline"
```
