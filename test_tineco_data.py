#!/usr/bin/env python3
"""Test script to examine Tineco API data without deploying to Home Assistant."""

import json
import sys
import os

# Add paths to import the Tineco client directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'tineco'))

from tineco_client_impl import TinecoClient


def test_tineco_data():
    """Test Tineco API and display all relevant data."""
    
    # Get credentials
    email = input("Enter Tineco email: ").strip()
    password = input("Enter Tineco password: ").strip()
    
    print("\n" + "="*80)
    print("TINECO API DATA TEST")
    print("="*80)
    
    # Create client
    client = TinecoClient()
    
    # Login
    print("\n[1/4] Logging in...")
    success, token, uid = client.login(email, password)
    if not success:
        print("❌ Login failed!")
        return
    print("✅ Login successful")
    
    # Get device list
    print("\n[2/4] Getting device list...")
    client.get_devices()
    if not client.device_list:
        print("❌ No devices found!")
        return
    
    print(f"✅ Found {len(client.device_list)} device(s)")
    
    # Display device list info
    print("\n" + "-"*80)
    print("DEVICE LIST DATA (for model/firmware)")
    print("-"*80)
    for i, device in enumerate(client.device_list):
        print(f"\nDevice {i+1}:")
        print(json.dumps(device, indent=2, default=str))
    
    # Get first device
    first_device = client.device_list[0]
    device_id = first_device.get("did") or first_device.get("deviceId")
    device_class = first_device.get("className", "")
    device_resource = first_device.get("resource", "")
    
    print(f"\n[3/4] Getting complete device info for device: {device_id}")
    
    # Get complete device info
    info = client.get_complete_device_info(device_id, device_class, device_resource)
    
    if not info:
        print("❌ Failed to get device info!")
        return
    
    print("✅ Got device info")
    
    # Display all endpoint data
    print("\n" + "-"*80)
    print("COMPLETE DEVICE INFO (all endpoints)")
    print("-"*80)
    print(json.dumps(info, indent=2, default=str))
    
    # Analyze specific fields for our sensors
    print("\n" + "="*80)
    print("SENSOR FIELD ANALYSIS")
    print("="*80)
    
    # Model analysis
    print("\n📱 MODEL SENSOR:")
    print("  Available fields in device list:")
    for key in ['deviceName', 'name', 'nick', 'model', 'deviceModel']:
        value = first_device.get(key)
        if value:
            starts_with_zero = str(value).startswith('0000')
            print(f"    {key}: '{value}' {'⚠️ STARTS WITH 0000' if starts_with_zero else '✓'}")
    
    # Firmware analysis
    print("\n💾 FIRMWARE SENSOR:")
    print("  Device list fields:")
    for key in ['firmwareVersion', 'fwVersion', 'version']:
        value = first_device.get(key)
        if value:
            # Check if printable
            printable = all(c.isprintable() and ord(c) < 128 for c in str(value))
            print(f"    {key}: '{value}' {'✓ PRINTABLE' if printable else '⚠️ HAS SPECIAL CHARS'}")
    
    print("\n  Endpoint fields:")
    for endpoint_key in ['gci', 'gav', 'gcf', 'cfp', 'query_mode']:
        if endpoint_key in info and info[endpoint_key]:
            endpoint_data = info[endpoint_key]
            if isinstance(endpoint_data, dict):
                for payload_key in ['payload', 'data']:
                    payload = endpoint_data.get(payload_key)
                    if isinstance(payload, dict):
                        for fw_key in ['firmware_version', 'fwVersion', 'firmwareVersion', 'fw', 'version', 'vv']:
                            if fw_key in payload:
                                print(f"    {endpoint_key}.{payload_key}.{fw_key}: '{payload[fw_key]}'")
    
    # Vacuum status analysis
    print("\n🧹 VACUUM STATUS SENSOR:")
    print("  Looking for wm, selfclean_process, station, sta, cleanway, selectmode fields...")
    
    def find_fields(obj, path=""):
        """Recursively find relevant fields."""
        results = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key.lower() in ['wm', 'selfclean_process', 'selfclean_progress', 'station', 'sta', 'cleanway', 'selectmode', 'wheel', 'msr']:
                    results.append((current_path, value))
                if isinstance(value, (dict, list)):
                    results.extend(find_fields(value, current_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                results.extend(find_fields(item, f"{path}[{i}]"))
        return results
    
    fields_found = find_fields(info)
    if fields_found:
        for path, value in fields_found:
            # Interpret wm value
            if 'wm' in path.lower():
                status_map = {0: "Idle", 1: "Idle", 2: "Charging", 3: "In Operation", 4: "In Operation", 8: "Docked/Standby", 10: "Unknown Mode 10"}
                status = status_map.get(value, f"Unknown Mode {value}")
                print(f"    {path}: {value} → {status}")
            else:
                print(f"    {path}: {value}")
    else:
        print("    ⚠️ No status fields found!")
    
    # Water tank analysis
    print("\n💧 WATER TANK SENSORS:")
    print("  Looking for wdt, mdt, wp, dv, vs, error codes...")
    
    def find_water_fields(obj, path=""):
        """Recursively find water tank fields."""
        results = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key.lower() in ['wdt', 'mdt', 'wp', 'dv', 'vs', 'vl', 'e1', 'e2', 'e3', 'water_level', 'water_status']:
                    results.append((current_path, key.lower(), value))
                if isinstance(value, (dict, list)):
                    results.extend(find_water_fields(value, current_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                results.extend(find_water_fields(item, f"{path}[{i}]"))
        return results
    
    water_fields = find_water_fields(info)
    if water_fields:
        for path, field, value in water_fields:
            if field == 'wdt':
                status = "Needs Refill" if value == 0 else "OK"
                print(f"    {path}: {value} → Clean Water Tank: {status}")
            elif field == 'mdt':
                status = "Needs Emptying" if value == 1 else "OK"
                print(f"    {path}: {value} → Dirty Water Tank: {status}")
            elif field == 'wp':
                print(f"    {path}: {value} → Water Pressure/Percentage")
            elif field == 'dv':
                print(f"    {path}: {value} → DV (device value?)")
            elif field == 'vs':
                print(f"    {path}: {value} → VS (vacuum/water status?)")
            elif field == 'vl':
                print(f"    {path}: {value} → VL (voice/volume level?)")
            elif field in ['e1', 'e2', 'e3']:
                error_meanings = {
                    'e1': 'Error 1',
                    'e2': 'Error 2 (Dirty Tank=64)',
                    'e3': 'Error 3'
                }
                if value != 0:
                    print(f"    {path}: {value} → {error_meanings[field]} ACTIVE")
                else:
                    print(f"    {path}: {value} → {error_meanings[field]} (None)")
    else:
        print("    ⚠️ No water tank fields found!")
    
    # Volume control test
    print("\n" + "="*80)
    print("VOLUME CONTROL TEST")
    print("="*80)
    
    print("\n[4/4] Testing volume control command...")
    
    # Check current volume state
    print("\n📢 Current volume/mute state:")
    for endpoint_key in ['gci', 'cfp']:
        if endpoint_key in info and isinstance(info[endpoint_key], dict):
            if 'vl' in info[endpoint_key]:
                vl_value = info[endpoint_key]['vl']
                state = "ON (Unmuted)" if vl_value == 1 else "OFF (Muted)"
                print(f"    {endpoint_key}.vl: {vl_value} → {state}")
    
    # Test volume control - automatically send ms=0
    print("\n🔧 Testing volume control with {'ms': 0}...")
    command = {"ms": 0}
    
    print(f"   Device ID: {device_id}")
    print(f"   Device Class: {device_class}")
    print(f"   Device Resource: {device_resource}")
    
    result = client.control_device(device_id, command, device_resource, device_class)
    
    if result:
        print("\n✅ Command sent successfully!")
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        # Wait and check new state
        import time
        print("\n⏳ Waiting 2 seconds for device to update...")
        time.sleep(2)
        
        print("\n🔄 Fetching updated device info...")
        updated_info = client.get_complete_device_info(device_id, device_class, device_resource)
        
        if updated_info:
            print("\n📢 Updated volume/mute state:")
            for endpoint_key in ['gci', 'cfp']:
                if endpoint_key in updated_info and isinstance(updated_info[endpoint_key], dict):
                    if 'vl' in updated_info[endpoint_key]:
                        vl_value = updated_info[endpoint_key]['vl']
                        state = "ON (Unmuted)" if vl_value == 1 else "OFF (Muted)"
                        print(f"    {endpoint_key}.vl: {vl_value} → {state}")
    else:
        print("\n❌ Command failed - no response received")
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        test_tineco_data()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
