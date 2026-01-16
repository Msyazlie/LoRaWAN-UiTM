"""
Safe Zone Alarm System

Logic: SAFE when beacon is NEAR (strong signal), ALARM when beacon moves AWAY (weak signal).

Use Case: Asset tracking - alarm when tagged item leaves the safe zone (e.g., different floor).

CORRECT LOGIC:
    RSSI > -70 dBm = SAFE (beacon nearby, safe zone) → Silence alarm
    RSSI ≤ -70 dBm = ALARM (beacon far, left safe zone) → Trigger alarm

Author: IoT Security System
Version: 3.2
Date: 2026-01-07
"""

import time
import json
import base64
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from src.services.event_manager import EventManager
from src.config.settings import (
    SAFE_RSSI_THRESHOLD, 
    load_devices, 
    get_floor_by_device, 
    get_macro_sensor_for_floor
)


# =============================================================================
# CONFIGURATION
# =============================================================================

class ProximityConfig:
    """Configuration constants for proximity alarm system."""
    
    # RSSI Threshold (dBm)
    # Below this = ALARM (weak signal / danger zone)
    # RSSI Threshold (dBm)
    # Below this = ALARM (weak signal / danger zone)
    RSSI_THRESHOLD = SAFE_RSSI_THRESHOLD
    
    # =================================================================
    # TARGET DEVICE (Update this to your Macro Sensor's DevEUI)
    # =================================================================
    MACRO_SENSOR_EUI = "70b3d5a4d31205cf"  # ← YOUR SENSOR EUI
    
    # Beacon Major ID (Must match your beacons)
    # Log shows "001064AF", so Major is likely "0010"
    BEACON_MAJOR = "0010"
    
    # =================================================================
    # MACRO SENSOR APPLICATION ID (CRITICAL!)
    # =================================================================
    # This MUST match the Application ID where the Macro Sensor is registered
    MACRO_SENSOR_APP_ID = "579dd7d2-1e4d-4e5c-b5ba-751f651142bb"  # ← MacroSensor app
    
    # =================================================================
    # FPort for Lansitec Commands
    # =================================================================
    # FPort 10 = Management/Configuration port for AC Search command
    FPORT = 10
    
    # =================================================================
    # Command Delay (CRITICAL)
    # =================================================================
    # LoRaWAN devices cannot process back-to-back downlinks.
    # This delay ensures UNMUTE is processed before TRIGGER arrives.
    COMMAND_DELAY = 2  # seconds
    
    # Debounce - weak signal must persist this long before alarm
    DEBOUNCE_SECONDS = 5
    
    # Hex Commands (based on Lansitec documentation)
    # Type 0xB (Alarm Config): B0 + MSGID + ParamType + Value
    CMD_VOLUME_HIGH = "B0000104"   # Set buzzer volume to 4 (loudest)
    CMD_VOLUME_MUTE = "B0000100"   # Mute buzzer (volume 0)
    CMD_DURATION = "B0000206"       # Set buzzer duration to 60s (06 * 10s)
    CMD_TRIGGER_BASE = "AC"         # Beacon search command prefix (Type 0xA, Cmd 0xC)


class SecurityZone(Enum):
    SAFE = "SAFE"
    WEAK = "WEAK"
    ALARM = "ALARM"


# Alias for compatibility
# ProximityConfig = SafeZoneConfig # This line is now redundant as SafeZoneConfig is renamed


@dataclass
class BeaconState:
    beacon_id: str
    zone: Optional[SecurityZone] = None
    last_rssi: int = -999
    last_seen: float = 0
    weak_start: Optional[float] = None
    alarm_active: bool = False
    initialized: bool = False
    current_location: str = "Unknown"


# =============================================================================
# GLOBAL STATE
# =============================================================================

_beacon_states: Dict[str, BeaconState] = {}
_msg_id_counter = 0
_app_id: Optional[str] = None


def set_app_id(app_id: str):
    global _app_id
    _app_id = app_id


def get_beacon_state(beacon_id: str) -> BeaconState:
    if beacon_id not in _beacon_states:
        _beacon_states[beacon_id] = BeaconState(beacon_id=beacon_id)
    return _beacon_states[beacon_id]


def get_all_beacon_states() -> Dict[str, Dict]:
    return {
        bid: {
            "id": state.beacon_id,
            "zone": state.zone.value if state.zone else "UNKNOWN",
            "state": state.zone.value if state.zone else "UNKNOWN",
            "rssi": state.last_rssi,
            "last_seen": state.last_seen,
            "alarm_active": state.alarm_active,
            "location": state.current_location
        }
        for bid, state in _beacon_states.items()
    }


# =============================================================================
# MAIN FUNCTION - SAFE ZONE LOGIC
# =============================================================================

def check_alarm_conditions(rssi: int, minor_id: str, mqtt_client: Any, gateway_eui: str = None) -> str:
    """
    Check alarm conditions based on location (Cross-Level Detection).
    
    LOGIC:
        1. Identify Detection Floor using 'gateway_eui'
        2. Identify Beacon Home Floor using 'minor_id' (from devices.json)
        3. If Detection Floor == Home Floor -> SAFE (Silence)
        4. If Detection Floor != Home Floor -> ALARM (Buzz Macro Sensor on Detection Floor)
    """
    global _app_id
    
    minor_id = minor_id.upper().zfill(4)
    state = get_beacon_state(minor_id)
    state.last_rssi = rssi
    state.last_seen = time.time()
    
    # Capture old state for event detection
    old_zone = state.zone

    # ---------------------------------------------------------
    # LOCATION-BASED LOGIC
    # ---------------------------------------------------------
    devices_config = load_devices()
    
    # 1. Find Detection Floor
    detection_floor = None
    if gateway_eui:
        detection_floor = get_floor_by_device(gateway_eui)
        
    detection_floor_id = detection_floor.get("id") if detection_floor else "UNKNOWN"
    detection_floor_name = detection_floor.get("name", "Unknown Floor") if detection_floor else "Unknown Floor"
    
    # Update Location State
    state.current_location = detection_floor_name

    # 2. Find Beacon Home Floor
    home_floor_id = "UNKNOWN"
    for b in devices_config.get("beacons", []):
        if b.get("id", "").upper() == minor_id:
            home_floor_id = b.get("home_floor_id")
            break
            
    print(f"📍 Beacon {minor_id} | RSSI {rssi} dBm | G/W: {gateway_eui} ({detection_floor_name})")
    
    # ---------------------------------------------------------
    # DETERMINE SAFE VS ALARM
    # ---------------------------------------------------------
    is_safe_zone = False
    
    # Logic: 
    #   ALARM if: (Wrong Floor) OR (Weak Signal)
    #   SAFE only if: (Correct Floor) AND (Strong Signal)
    
    is_wrong_floor = False
    is_weak_signal = rssi < ProximityConfig.RSSI_THRESHOLD
    
    # Check Location Correctness
    if detection_floor_id != "UNKNOWN" and home_floor_id != "UNKNOWN":
        if detection_floor_id != home_floor_id:
            is_wrong_floor = True
            print(f"   ❌ MISMATCH: Home {home_floor_id} != Detected {detection_floor_id}")
        else:
            print(f"   ✅ MATCH: Home {home_floor_id} == Detected {detection_floor_id}")
            
    # Determine Final State
    if is_wrong_floor:
        is_safe_zone = False
        print(f"   🚨 ALARM REASON: WRONG FLOOR")
    elif is_weak_signal:
        is_safe_zone = False
        print(f"   🚨 ALARM REASON: WEAK SIGNAL ({rssi} <= {ProximityConfig.RSSI_THRESHOLD})")
    else:
        is_safe_zone = True
        print(f"   🟢 SAFE REASON: CORRECT FLOOR + STRONG SIGNAL")

    # Determine Target Sensor (The one on the DETECTION floor)
    target_sensor_eui = detection_floor.get("macro_sensor_eui") if detection_floor else ProximityConfig.MACRO_SENSOR_EUI
    
    # =========================================================
    # STARTUP SILENCE (First Detection)
    # =========================================================
    if not state.initialized:
        print(f"   🚀 STARTUP: First detection of {minor_id} - Forcing SILENCE")
        stop_alarm(mqtt_client, target_sensor_eui, minor_id)
        
        # Initialize state
        state.initialized = True
        state.zone = SecurityZone.SAFE
        state.weak_start = None
        state.current_location = detection_floor_name
        
        return "SAFE"
    
    # =========================================================
    # SAFE ZONE (Correct Floor)
    # ACTION: SILENCE
    # =========================================================
    if is_safe_zone:
        print(f" → 🟢 SAFE ZONE (Correct Floor)")
        
        if state.alarm_active or not state.initialized:
            if not state.initialized:
                print(f"   🔄 First detection - Forcing state sync (SILENCE)")
            else:
                print(f"   ✅ Returned to Home Floor - Stopping alarm on {target_sensor_eui}")
                
            stop_alarm(mqtt_client, target_sensor_eui, minor_id)
            state.alarm_active = False
            state.initialized = True
        
        state.zone = SecurityZone.SAFE
        state.weak_start = None
        state.initialized = True
        
        if old_zone is not None and old_zone != state.zone:
            EventManager.emit("beacon_state_change", {
                "beacon_id": minor_id,
                "old_state": old_zone.value if old_zone else "UNKNOWN",
                "new_state": state.zone.value,
                "rssi": rssi
            })
            
        return "SAFE"

    # =========================================================
    # ALARM ZONE (Wrong Floor)
    # ACTION: TRIGGER ALARM
    # =========================================================
    else:
        # Start debounce timer for ALARM
        if state.weak_start is None:
            state.weak_start = time.time()
            state.zone = SecurityZone.ALARM # Using ALARM/WEAK pending confirmation
            print(f" → � LEAVING SAFE ZONE - monitoring...")
            
            if old_zone is not None and old_zone != state.zone:
                 EventManager.emit("beacon_state_change", {
                    "beacon_id": minor_id,
                    "old_state": old_zone.value if old_zone else "UNKNOWN",
                    "new_state": state.zone.value,
                    "rssi": rssi
                })
            return "ALARM"

        duration = time.time() - state.weak_start
        
        # Trigger buzz if signal remains weak (Far away)
        if duration >= ProximityConfig.DEBOUNCE_SECONDS:
            print(f" → � ALARM ZONE (Confirmed Away for {duration:.1f}s)")
            
            if not state.alarm_active:
                print(f"\n🚨 ═══════════════════════════════════════════")
                print(f"🚨  ALARM ZONE ACTIVATION (Buzzing)")
                print(f"🚨  Beacon: {minor_id}")
                print(f"🚨  Location: {detection_floor_name} (Wrong Floor!)")
                print(f"🚨  Target Sensor: {target_sensor_eui}")
                print(f"🚨 ═══════════════════════════════════════════\n")
                
                trigger_alarm_with_sequence(mqtt_client, target_sensor_eui, minor_id)
                state.alarm_active = True
                
            state.zone = SecurityZone.ALARM
            return "ALARM"
        else:
             print(f" → � LEAVING ({duration:.1f}s / {ProximityConfig.DEBOUNCE_SECONDS}s)")
             return "ALARM"


def check_floor_security(rssi: int, minor_id: str, mqtt_client: Any) -> SecurityZone:
    result = check_alarm_conditions(rssi, minor_id, mqtt_client)
    return SecurityZone[result]


# =============================================================================
# ALARM TRIGGER - SEND AC SEARCH BEACON COMMAND
# =============================================================================

def trigger_alarm_with_sequence(mqtt_client: Any, sensor_eui: str, beacon_minor: str) -> bool:
    """
    Trigger alarm by sending UNMUTE + AC Search Beacon commands.
    
    Sequence:
    1. Send B0000101 (UNMUTE - Set Volume HIGH)
    2. Wait briefly for device to process
    3. Send AC + MsgID + Minor (Search Beacon)
    
    Args:
        mqtt_client: MQTT client for publishing downlinks
        sensor_eui: Target sensor's DevEUI
        beacon_minor: Beacon Minor ID (e.g., "64B0", "64AF")
    
    Returns:
        bool: True if commands sent successfully
    """
    global _msg_id_counter
    
    minor = beacon_minor.upper().zfill(4)
    
    print(f"\n🚨 TRIGGER ALARM SEQUENCE")
    print(f"   Target Sensor: {sensor_eui}")
    print(f"   Beacon Minor: {minor}")
    
    # Step 1: Set buzzer volume to 4 (loudest)
    print(f"\n   📢 Step 1: Set Volume to LOUDEST (4)")
    _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        ProximityConfig.CMD_VOLUME_HIGH,  # B0000104
        "VOLUME (Level=4)"
    )
    
    time.sleep(ProximityConfig.COMMAND_DELAY)
    
    # Step 2: Set buzzer duration to 60s
    print(f"\n   ⏱️ Step 2: Set Duration to 60s")
    _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        ProximityConfig.CMD_DURATION,  # B0000206
        "DURATION (60s)"
    )
    
    time.sleep(ProximityConfig.COMMAND_DELAY)
    
    # Step 3: Send AC Search Beacon command
    # MsgID increments to ensure each command is unique
    msg_id = f"{_msg_id_counter:02X}"
    _msg_id_counter = (_msg_id_counter + 1) % 256
    
    trigger_hex = f"AC{msg_id}{ProximityConfig.BEACON_MAJOR}{minor}"  # AC + MsgID + Major + Minor
    
    print(f"\n   🔔 Step 3: SEARCH BEACON ({trigger_hex})")
    trigger_success = _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        trigger_hex, 
        f"SEARCH BEACON ({trigger_hex})"
    )
    
    if trigger_success:
        print(f"\n   ✅ Alarm trigger sequence complete!")
    else:
        print(f"\n   ❌ Failed to send search command!")
    
    return trigger_success


def stop_alarm(mqtt_client: Any, sensor_eui: str, beacon_minor: str) -> bool:
    """
    Stop alarm by sending the B0000100 MUTE command.
    
    This sets the buzzer volume to 0, which stops the sound.
    
    Args:
        mqtt_client: MQTT client for publishing downlinks
        sensor_eui: Target sensor's DevEUI
        beacon_minor: Beacon Minor ID (not used, but kept for consistency)
    
    Returns:
        bool: True if command sent successfully
    """
    # B0000100 = Set volume to 0 (MUTE/STOP)
    stop_hex = "B0000100"
    
    print(f"   🔇 STOP ALARM: {stop_hex} (Mute)")
    
    success = _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        stop_hex, 
        "MUTE (Volume=0)"
    )
    
    return success


def unmute_alarm(mqtt_client: Any, sensor_eui: str, beacon_minor: str) -> bool:
    """
    Unmute alarm by sending the B0000101 command (Volume HIGH).
    
    This sets the buzzer volume to 3 (HIGH), enabling it to make sound.
    
    Args:
        mqtt_client: MQTT client for publishing downlinks
        sensor_eui: Target sensor's DevEUI
        beacon_minor: Beacon Minor ID (not used, but kept for consistency)
    
    Returns:
        bool: True if command sent successfully
    """
    # B0000103 = Set volume to 3 (HIGH/UNMUTE)
    unmute_hex = "B0000101"
    
    print(f"   📢 UNMUTE ALARM: {unmute_hex} (Volume HIGH)")
    
    success = _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        unmute_hex, 
        "UNMUTE (Volume=3)"
    )
    
    return success


def start_alarm(mqtt_client: Any, sensor_eui: str, beacon_minor: str) -> bool:
    """
    Start alarm by sending UNMUTE + AC Search Beacon commands.
    
    This is the opposite of stop_alarm() - it enables the buzzer and triggers search.
    
    Args:
        mqtt_client: MQTT client for publishing downlinks
        sensor_eui: Target sensor's DevEUI
        beacon_minor: Beacon Minor ID to search for
    
    Returns:
        bool: True if commands sent successfully
    """
    
    print(f"\n   🔔 START ALARM for beacon {beacon_minor}")
    return trigger_alarm_with_sequence(mqtt_client, sensor_eui, beacon_minor)

def _send_downlink_to_device(mqtt_client: Any, device_eui: str, hex_cmd: str, cmd_name: str) -> bool:
    """
    Send a downlink command to a specific device.
    
    Args:
        mqtt_client: MQTT client
        device_eui: Target device's DevEUI
        hex_cmd: Hex command string (e.g., "B0000101")
        cmd_name: Human-readable command name for logging
    
    Returns:
        bool: True if published successfully
    """
    global _app_id
    
    # Use the target sensor EUI passed in, or fallback to default
    target_eui = device_eui if device_eui else ProximityConfig.MACRO_SENSOR_EUI
    
    # Use Dynamic App ID (captured from uplinks)
    # If not yet captured, fallback to hardcoded but print warning
    app_id = _app_id
    
    if not app_id:
        print("   ⚠️ WARNING: No dynamic App ID captured yet! Falling back to Config ID.")
        app_id = ProximityConfig.MACRO_SENSOR_APP_ID
    
    try:
        topic = f"application/{app_id}/device/{target_eui}/command/down"
        
        data_bytes = bytes.fromhex(hex_cmd)
        data_b64 = base64.b64encode(data_bytes).decode('utf-8')
        
        payload = {
            "devEui": target_eui,
            "confirmed": False,
            "fPort": ProximityConfig.FPORT,
            "data": data_b64
        }
        
        # DEBUG: Print full details
        print(f"   📡 {cmd_name}: {hex_cmd} → FPort {ProximityConfig.FPORT}")
        print(f"   📝 Topic: {topic}")
        print(f"   📝 App ID: {app_id}")
        print(f"   📝 Payload: {json.dumps(payload)}")
        
        mqtt_client.publish(topic, json.dumps(payload))
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


# =============================================================================
# UTILITY
# =============================================================================

def manual_trigger_alarm(mqtt_client: Any, minor_id: str) -> bool:
    """Manually trigger alarm for a specific beacon."""
    print(f"\n🔔 Manual Alarm: {minor_id}")
    return trigger_alarm_with_sequence(
        mqtt_client, 
        ProximityConfig.MACRO_SENSOR_EUI, 
        minor_id
    )


def manual_silence_alarm(mqtt_client: Any) -> bool:
    """Manually silence the alarm."""
    print(f"\n🔇 Manual Silence")
    return _send_downlink_to_device(
        mqtt_client,
        ProximityConfig.MACRO_SENSOR_EUI,
        ProximityConfig.CMD_VOLUME_MUTE,
        "SILENCE"
    )
