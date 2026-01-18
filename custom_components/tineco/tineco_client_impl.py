#!/usr/bin/env python3
"""
Tineco IoT API Client - Complete implementation with CLI interface
Combines TinecoClient library + Interactive device query tool
Based on reverse-engineered code from Tineco Android app (IotUtils.java)
"""

import requests
import hashlib
import time
import json
from typing import Dict, Optional, Tuple


class TinecoClient:
    """Tineco API client with automatic authSign calculation"""
    
    # Constants from decompiled BaseTinecoLifeApplication.java
    AUTH_APPKEY = "1538105560006"
    APP_SECRET = "fb7045ebb8ae5297bca45cbf5a5597ab"
    
    # Alternative auth constants for device list endpoint (from BaseUpLoadData.java)
    AUTH_APPKEY_AUTHCODE = "1538103661113"
    APP_SECRET_AUTHCODE = "197472fcef3935ebc330657266992b99"
    
    # Default configuration
    DEVICE_ID = "57938f751acc6897088c718770edcd00"
    REGION = "IE"
    LANGUAGE = "EN_US"
    APP_VERSION = "1.7.0"
    STORE = "google_play"
    AUTH_TIMEZONE = "Europe/London"
    
    # API base
    API_BASE = "https://qas-gl-{region}-api.tineco.com/v1/private/{region}/{language}/{device_id}/global_e/{version}/{store}/1"
    
    # Headers matching official app
    DEFAULT_HEADERS = {
        "User-Agent": "okhttp/5.3.2",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive"
    }
    
    def __init__(self, region: str = REGION, language: str = LANGUAGE):
        """Initialize Tineco client"""
        self.region = region
        self.language = language
        self.access_token = ""
        self.uid = ""
        self.auth_code = ""
        self.iot_token = ""
        self.iot_resource = ""
        self.device_list = []
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        
        # IoT API endpoints
        self.IOT_API_BASE = "https://api-ngiot.dc-eu.ww.ecouser.net/api/iot/endpoint/control"
        self.IOT_LOGIN_ENDPOINT = "https://api-base.dc-eu.ww.ecouser.net/api/users/user.do"
    
    def _md5_hash(self, text: str) -> str:
        """Calculate MD5 hash"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _calculate_auth_sign(self, custom_params: Dict[str, str],  
                            timestamp: int, uid: str = "", 
                            access_token: str = "") -> str:
        """Calculate authSign using reverse-engineered algorithm"""
        params = [
            f"authTimespan={timestamp}",
            f"authTimeZone={self.AUTH_TIMEZONE}",
            f"country={self.region}",
            f"lang={self.language}",
            "appCode=global_e",
            f"appVersion={self.APP_VERSION}",
            f"deviceId={self.DEVICE_ID}",
            f"channel={self.STORE}",
            "deviceType=1",
            f"uid={uid}",
            f"accessToken={access_token}"
        ]
        
        for key, value in custom_params.items():
            params.append(f"{key}={value}")
        
        params.sort()
        auth_string = self.AUTH_APPKEY + "".join(params) + self.APP_SECRET
        return self._md5_hash(auth_string)
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Login to Tineco API with email and password"""
        try:
            timestamp = int(time.time() * 1000)
            password_md5 = self._md5_hash(password)
            
            custom_params = {
                "account": email,
                "password": password_md5
            }
            
            auth_sign = self._calculate_auth_sign(custom_params, timestamp, uid="", access_token="")
            
            url = (f"https://qas-gl-{self.region.lower()}-api.tineco.com/v1/private/"
                   f"{self.region}/{self.language}/{self.DEVICE_ID}/global_e/"
                   f"{self.APP_VERSION}/{self.STORE}/1/user/login")
            
            query_params = {
                "authAppkey": self.AUTH_APPKEY,
                "authSign": auth_sign,
                "authTimeZone": self.AUTH_TIMEZONE,
                "authTimespan": timestamp,
                "account": email,
                "password": password_md5,
                "uid": "",
                "accessToken": ""
            }
            
            print(f"[INFO] Logging in: {email}")
            response = self.session.get(url, params=query_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                code = data.get("code")
                
                if code == "0000":
                    response_data = data.get("data", data)
                    self.access_token = response_data.get("accessToken", "")
                    self.uid = response_data.get("uid", "")
                    user_id = self.uid
                    username = response_data.get("userName", "")
                    
                    print(f"[OK] Login successful!")
                    print(f"    User ID: {user_id}")
                    print(f"    Username: {username}")
                    return True, self.access_token, user_id
                else:
                    msg = data.get("msg", "")
                    print(f"[ERROR] Login failed: {msg} (Code: {code})")
                    return False, None, None
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return False, None, None
                
        except Exception as e:
            print(f"[ERROR] Error: {str(e)}")
            return False, None, None
    
    def _get_auth_code(self) -> bool:
        """Get authCode from /global/auth/getAuthCode endpoint"""
        if not self.uid or not self.access_token:
            print("[ERROR] REST login required before getting authCode")
            return False
        
        try:
            url = (f"https://qas-gl-{self.region.lower()}-openapi.tineco.com/v1/"
                   f"global/auth/getAuthCode")
            
            timestamp = int(time.time() * 1000)
            
            params_list = [
                f"authTimespan={timestamp}",
                "appCode=global_e",
                f"appVersion={self.APP_VERSION}",
                "openId=global",
                f"uid={self.uid}",
                f"accessToken={self.access_token}",
                f"deviceId={self.DEVICE_ID}"
            ]
            
            params_list.sort()
            auth_string = self.AUTH_APPKEY_AUTHCODE + "".join(params_list) + self.APP_SECRET_AUTHCODE
            auth_sign = self._md5_hash(auth_string)
            
            query_params = {
                "authAppkey": self.AUTH_APPKEY_AUTHCODE,
                "authSign": auth_sign,
                "uid": self.uid,
                "accessToken": self.access_token,
                "deviceId": self.DEVICE_ID,
                "appCode": "global_e",
                "appVersion": self.APP_VERSION,
                "authTimespan": timestamp
            }
            
            print(f"[INFO] Getting authCode...")
            response = self.session.get(url, params=query_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                code = data.get("code")
                
                if code == "0000" or code == 0:
                    auth_code_data = data.get("data", data)
                    if isinstance(auth_code_data, dict):
                        self.auth_code = auth_code_data.get("authCode", "")
                    else:
                        self.auth_code = auth_code_data if isinstance(auth_code_data, str) else ""
                    
                    if not self.auth_code:
                        print("[ERROR] authCode not in response")
                        return False
                    
                    print(f"[OK] Got authCode!")
                    print(f"    authCode: {self.auth_code[:20]}...")
                    return True
                else:
                    print(f"[ERROR] Failed to get authCode: {data.get('msg', 'Unknown error')}")
                    return False
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error getting authCode: {str(e)}")
            return False
    
    def _iot_login(self) -> bool:
        """Login to IoT service to get token and resource for device list API"""
        if not self.uid or not self.auth_code:
            print("[ERROR] REST login and authCode required before IoT login")
            return False
        
        try:
            import uuid
            device_uuid = str(uuid.uuid4())
            timestamp = int(time.time() * 1000)
            
            payload = {
                "todo": "loginByItToken",
                "userId": self.uid,
                "token": self.auth_code,
                "realm": "ecouser.net",
                "edition": "default",
                "resource": device_uuid,
                "last": "",
                "country": self.region,
                "org": "TEKWW"
            }
            
            print(f"[INFO] Performing IoT login...")
            response = self.session.post(self.IOT_LOGIN_ENDPOINT, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", "")
                
                if result == "ok":
                    self.iot_token = data.get("token", "")
                    self.iot_resource = data.get("resource", device_uuid)
                    
                    if "userId" in data:
                        self.uid = data.get("userId")
                    
                    print(f"[OK] IoT login successful!")
                    print(f"    IoT Token: {self.iot_token[:20]}...")
                    print(f"    IoT Resource: {self.iot_resource}")
                    return True
                else:
                    error = data.get("error", "Unknown error")
                    print(f"[ERROR] IoT login failed: {error}")
                    return False
            else:
                print(f"[ERROR] IoT login HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] IoT login error: {str(e)}")
            return False
    
    def get_devices(self) -> Optional[Dict]:
        """Get list of devices for the logged-in user"""
        if not self.access_token or not self.uid:
            print("[ERROR] Not logged in. Call login() first.")
            return None
        
        if not self.auth_code:
            print("[INFO] Getting authCode for device access...")
            if not self._get_auth_code():
                print("[ERROR] Failed to get authCode")
                return None
        
        if not self.iot_token:
            print("[INFO] Performing IoT login to get device credentials...")
            if not self._iot_login():
                print("[ERROR] IoT login failed, cannot get device list")
                return None
        
        try:
            url = (f"https://qas-gl-{self.region.lower()}-openapi.tineco.com/v1/"
                   f"global/device/getDeviceListV2")
            
            timestamp = int(time.time() * 1000)
            
            params_list = [
                f"authTimespan={timestamp}",
                f"lang={self.language}",
                "appCode=global_e",
                f"appVersion={self.APP_VERSION}",
                f"deviceId={self.DEVICE_ID}",
                "openId=global",
                f"uid={self.uid}",
                f"accessToken={self.access_token}",
                f"resource={self.iot_resource}",
                f"token={self.iot_token}",
                f"userId={self.uid}",
                "deviceType=1",
                "refresh=false"
            ]
            
            params_list.sort()
            auth_string = self.AUTH_APPKEY_AUTHCODE + "".join(params_list) + self.APP_SECRET_AUTHCODE
            auth_sign = self._md5_hash(auth_string)
            
            query_params = {
                "authAppkey": self.AUTH_APPKEY_AUTHCODE,
                "authSign": auth_sign,
                "uid": self.uid,
                "accessToken": self.access_token,
                "appCode": "global_e",
                "appVersion": self.APP_VERSION,
                "deviceId": self.DEVICE_ID,
                "authTimespan": timestamp,
                "resource": self.iot_resource,
                "token": self.iot_token,
                "userId": self.uid,
                "lang": self.language,
                "deviceType": "1",
                "refresh": "false"
            }
            
            print(f"[INFO] Fetching device list...")
            response = self.session.get(url, params=query_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0000" or data.get("code") == 0:
                    payload = data.get("payload", data.get("data", data))
                    if isinstance(payload, dict):
                        self.device_list = payload.get("deviceList", payload.get("userDeviceList", []))
                    else:
                        self.device_list = payload if isinstance(payload, list) else []
                    
                    print(f"[OK] Found {len(self.device_list)} device(s)")
                    for device in self.device_list:
                        device_name = device.get('deviceName', device.get('name', 'Unknown'))
                        device_id = device.get('deviceId', device.get('id', 'Unknown'))
                        print(f"    - {device_name} ({device_id})")
                    return data
                else:
                    print(f"[ERROR] Failed to get devices: {data.get('msg', data.get('message', 'Unknown error'))}")
                    return None
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error getting devices: {str(e)}")
            return None
    
    def get_device_status(self, device_id: str, device_class: str = "", 
                         device_resource: str = "", session_id: str = "") -> Optional[Dict]:
        """Get device status from IoT API"""
        if not self.access_token:
            print("[ERROR] Not logged in. Call login() first.")
            return None
        
        try:
            import random
            import string
            
            if not session_id:
                chars = string.ascii_letters + string.digits
                session_id = ''.join(random.choice(chars) for _ in range(16))
            
            params = {
                "ct": "q",
                "eid": device_id,
                "fmt": "j",
                "apn": "QueryMode",
                "si": session_id
            }
            
            if device_class:
                params["et"] = device_class
            if device_resource:
                params["er"] = device_resource
            
            headers = {
                "Authorization": f"Bearer {self.iot_token if self.iot_token else self.access_token}",
                "X-ECO-REQUEST-ID": session_id
            }
            
            print(f"[INFO] Querying device {device_id}...")
            response = self.session.post(self.IOT_API_BASE, params=params, headers=headers, timeout=10)
            
            ngiot_ret = response.headers.get("X-NGIOT-RET", "")
            
            if response.status_code == 200:
                if ngiot_ret == "ok":
                    print(f"[OK] IoT endpoint returned success")
                    if response.text:
                        try:
                            return response.json()
                        except:
                            return {"status": "ok", "session_id": session_id}
                    else:
                        return {"status": "ok", "session_id": session_id}
                else:
                    if response.text:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and ("code" in data and data.get("code") == "0000" or "payload" in data):
                                print(f"[OK] Device status retrieved successfully")
                                return data
                        except:
                            pass
                    return None
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error getting device status: {str(e)}")
            return None
    
    def _send_iot_query(self, device_id: str, action: str, 
                        device_class: str = "", device_resource: str = "",
                        session_id: str = "") -> Optional[Dict]:
        """Internal method to send IoT query actions"""
        if not self.access_token:
            print("[ERROR] Not logged in. Call login() first.")
            return None
        
        try:
            import random
            import string
            
            if not session_id:
                chars = string.ascii_letters + string.digits
                session_id = ''.join(random.choice(chars) for _ in range(16))
            
            params = {
                "ct": "q",
                "eid": device_id,
                "fmt": "j",
                "apn": action,
                "si": session_id
            }
            
            if device_class:
                params["et"] = device_class
            if device_resource:
                params["er"] = device_resource
            
            headers = {
                "Authorization": f"Bearer {self.iot_token if self.iot_token else self.access_token}",
                "X-ECO-REQUEST-ID": session_id
            }
            
            print(f"[INFO] Querying device with action: {action}")
            response = self.session.post(self.IOT_API_BASE, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                ngiot_ret = response.headers.get("X-NGIOT-RET", "")
                
                if ngiot_ret == "ok":
                    print(f"[OK] Action '{action}' successful")
                    if response.text:
                        try:
                            return response.json()
                        except:
                            return {"status": "ok", "action": action}
                    else:
                        return {"status": "ok", "action": action}
                else:
                    print(f"[ERROR] Query failed")
                    return None
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error in query: {str(e)}")
            return None
    
    def get_controller_info(self, device_id: str, device_class: str = "",
                           device_resource: str = "") -> Optional[Dict]:
        """Get controller information (GCI - Get Controller Info)"""
        return self._send_iot_query(device_id, "gci", device_class, device_resource)
    
    def get_api_version(self, device_id: str, device_class: str = "",
                       device_resource: str = "") -> Optional[Dict]:
        """Get API version (GAV - Get API Version)"""
        return self._send_iot_query(device_id, "gav", device_class, device_resource)
    
    def get_config_file(self, device_id: str, device_class: str = "",
                       device_resource: str = "") -> Optional[Dict]:
        """Get configuration file (GCF - Get Config File)"""
        return self._send_iot_query(device_id, "gcf", device_class, device_resource)
    
    def get_device_config_point(self, device_id: str, device_class: str = "",
                               device_resource: str = "") -> Optional[Dict]:
        """Get config point (CFP - Config File Point)"""
        return self._send_iot_query(device_id, "cfp", device_class, device_resource)
    
    def query_device_mode(self, device_id: str, device_class: str = "",
                         device_resource: str = "") -> Optional[Dict]:
        """Query device operating mode (QueryMode)"""
        return self._send_iot_query(device_id, "QueryMode", device_class, device_resource)
    
    def get_complete_device_info(self, device_id: str, device_class: str = "",
                                device_resource: str = "") -> Dict:
        """Get complete device information by querying all available endpoints"""
        print(f"\n[INFO] Retrieving complete device information for {device_id}...")
        
        info = {}
        
        try:
            print("[INFO] Getting controller info (GCI)...")
            gci = self.get_controller_info(device_id, device_class, device_resource)
            if gci:
                info['gci'] = gci
            
            print("[INFO] Getting API version (GAV)...")
            gav = self.get_api_version(device_id, device_class, device_resource)
            if gav:
                info['gav'] = gav
            
            print("[INFO] Getting config file (GCF)...")
            gcf = self.get_config_file(device_id, device_class, device_resource)
            if gcf:
                info['gcf'] = gcf
            
            print("[INFO] Getting config point (CFP)...")
            cfp = self.get_device_config_point(device_id, device_class, device_resource)
            if cfp:
                info['cfp'] = cfp
            
            print("[INFO] Getting device modes (QueryMode)...")
            query_mode = self.query_device_mode(device_id, device_class, device_resource)
            if query_mode:
                info['query_mode'] = query_mode
            
            print(f"[OK] Retrieved {len(info)} information sources")
            return info
            
        except Exception as e:
            print(f"[ERROR] Error retrieving complete device info: {str(e)}")
            return info
    
    def control_device(self, device_id: str, command: Dict, 
                      device_sn: str = "", session_id: str = "") -> Optional[Dict]:
        """Send control command to device via IoT API"""
        if not self.access_token:
            print("[ERROR] Not logged in. Call login() first.")
            return None
        
        try:
            params = {
                "ct": "i",
                "eid": device_id,
                "fmt": "j"
            }
            
            if session_id:
                params["si"] = session_id
            if device_sn:
                params["er"] = device_sn
            
            params["accessToken"] = self.access_token
            params["uid"] = self.uid
            
            print(f"[INFO] Sending command to device {device_id}...")
            response = self.session.post(self.IOT_API_BASE, params=params, json=command, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "code" in data and data.get("code") == "0000":
                    print(f"[OK] Command sent successfully")
                    return data
                else:
                    print(f"[ERROR] Command failed: {data}")
                    return data
            else:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error sending command: {str(e)}")
            return None


def print_json(data, indent=2):
    """Pretty print JSON data"""
    try:
        if isinstance(data, dict):
            print(json.dumps(data, indent=indent))
        else:
            print(data)
    except:
        print(data)


def main():
    """Interactive device query tool"""
    print("=" * 80)
    print("Tineco Device Information Retrieval")
    print("=" * 80)
    print()
    
    client = TinecoClient()
    
    # Step 1: Authentication
    print("[STEP 1] Authentication")
    print("-" * 80)
    
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()
    
    success, token, user_id = client.login(email, password)
    
    if not success:
        print("[ERROR] Login failed!")
        return 1
    
    print(f"[OK] Login successful!")
    print(f"    User ID: {user_id}")
    print()
    
    # Step 2: Get devices
    print("[STEP 2] Get Devices")
    print("-" * 80)
    
    devices = client.get_devices()
    
    if not devices or not client.device_list:
        print("[ERROR] No devices found!")
        return 1
    
    print(f"[OK] Found {len(client.device_list)} device(s)")
    
    for i, device in enumerate(client.device_list, 1):
        name = device.get('nick') or device.get('deviceName', 'Unknown')
        device_id = device.get('did') or device.get('deviceId')
        print(f"    {i}. {name} ({device_id})")
    
    print()
    
    # Step 3: Select device
    print("[STEP 3] Select Device")
    print("-" * 80)
    
    if len(client.device_list) == 1:
        device = client.device_list[0]
        print(f"[->] Using device: {device.get('nick') or device.get('deviceName')}")
    else:
        idx = int(input(f"Enter device number (1-{len(client.device_list)}): ")) - 1
        device = client.device_list[idx]
    
    device_id = device.get('did') or device.get('deviceId')
    device_class = device.get('className', '')
    device_resource = device.get('resource', '')
    device_name = device.get('nick') or device.get('deviceName', 'Unknown')
    
    print(f"[OK] Selected: {device_name}")
    print(f"    ID: {device_id}")
    print(f"    Class: {device_class}")
    print(f"    Resource: {device_resource}")
    print()
    
    # Step 4: Query all device information
    print("[STEP 4] Query Device Information")
    print("-" * 80)
    print()
    
    print("[GCI] Get Controller Info")
    print("    Retrieves: Firmware version, hardware info, device capabilities")
    gci = client.get_controller_info(device_id, device_class, device_resource)
    if gci:
        print("[OK] Success:")
        print_json(gci, indent=6)
    else:
        print("[ERROR] Failed to retrieve")
    print()
    
    print("[GAV] Get API Version")
    print("    Retrieves: Device API version support")
    gav = client.get_api_version(device_id, device_class, device_resource)
    if gav:
        print("[OK] Success:")
        print_json(gav, indent=6)
    else:
        print("[ERROR] Failed to retrieve")
    print()
    
    print("[GCF] Get Config File")
    print("    Retrieves: Device configuration settings")
    gcf = client.get_config_file(device_id, device_class, device_resource)
    if gcf:
        print("[OK] Success:")
        print_json(gcf, indent=6)
    else:
        print("[ERROR] Failed to retrieve")
    print()
    
    print("[CFP] Get Config Point")
    print("    Retrieves: Specific configuration point data")
    cfp = client.get_device_config_point(device_id, device_class, device_resource)
    if cfp:
        print("[OK] Success:")
        print_json(cfp, indent=6)
    else:
        print("[ERROR] Failed to retrieve")
    print()
    
    print("[QueryMode] Get Device Modes")
    print("    Retrieves: Current and available device modes")
    modes = client.query_device_mode(device_id, device_class, device_resource)
    if modes:
        print("[OK] Success:")
        print_json(modes, indent=6)
    else:
        print("[ERROR] Failed to retrieve")
    print()
    
    # Step 5: Complete Device Information
    print("[STEP 5] Complete Device Information")
    print("-" * 80)
    print()
    
    print("Retrieving complete device information (all queries at once)...")
    complete_info = client.get_complete_device_info(device_id, device_class, device_resource)
    
    print(f"\n[OK] Retrieved information from {len(complete_info)} endpoints:")
    for key, value in complete_info.items():
        if value:
            size = len(json.dumps(value))
            print(f"    [OK] {key.upper():15} - {size:,} bytes")
        else:
            print(f"    [ERROR] {key.upper():15} - Failed")
    
    print()
    print("=" * 80)
    print("Device information retrieval complete!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
