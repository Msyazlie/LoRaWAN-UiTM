"""
Safe Zone Alarm System

Logic: SAFE when beacon is NEAR (strong signal), ALARM when beacon moves AWAY (weak signal).

Use Case: Asset tracking - alarm when tagged item leaves the safe zone (e.g., different floor).

CORRECT LOGIC:
    RSSI > -80 dBm = SAFE (beacon nearby, same floor) → Silence alarm
    RSSI ≤ -80 dBm = ALARM (beacon far, different floor) → Trigger alarm

Author: IoT Security System
Version: 3.1
Date: 2025-12-24
"""

import time
import json
import base64
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


# =============================================================================
# CONFIGURATION
# =============================================================================

class ProximityConfig:
    """Configuration constants for proximity alarm system."""
    
    # RSSI Threshold (dBm)
    # Below this = ALARM (weak signal / danger zone)
    RSSI_THRESHOLD = -85
    
    # =================================================================
    # TARGET DEVICE (Update this to your Macro Sensor's DevEUI)
    # =================================================================
    MACRO_SENSOR_EUI = "70b3d5a4d31205cf"  # ← YOUR SENSOR EUI
    
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
    
    # Hex Commands
    CMD_VOLUME_HIGH = "B0000103"   # Set buzzer volume to HIGH (3)
    CMD_VOLUME_MUTE = "B0000100"   # Mute buzzer (volume 0)
    CMD_TRIGGER_BASE = "AC"        # Beacon search command prefix


class SecurityZone(Enum):
    SAFE = "SAFE"
    WEAK = "WEAK"
    ALARM = "ALARM"


# Alias for compatibility
# ProximityConfig = SafeZoneConfig # This line is now redundant as SafeZoneConfig is renamed


@dataclass
class BeaconState:
    beacon_id: str
    zone: SecurityZone = SecurityZone.SAFE
    last_rssi: int = -999
    last_seen: float = 0
    weak_start: Optional[float] = None
    alarm_active: bool = False


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
            "zone": state.zone.value,
            "state": state.zone.value,
            "rssi": state.last_rssi,
            "last_seen": state.last_seen,
            "alarm_active": state.alarm_active
        }
        for bid, state in _beacon_states.items()
    }


# =============================================================================
# MAIN FUNCTION - SAFE ZONE LOGIC
# =============================================================================

def check_alarm_conditions(rssi: int, minor_id: str, mqtt_client: Any) -> str:
    """
    Check safe zone alarm conditions.
    
    SAFE ZONE LOGIC:
        RSSI > -80 dBm = SAFE (beacon nearby, same floor)
        RSSI ≤ -80 dBm = ALARM (beacon far away, different floor)
    """
    global _app_id
    
    minor_id = minor_id.upper().zfill(4)
    state = get_beacon_state(minor_id)
    state.last_rssi = rssi
    state.last_seen = time.time()
    
    print(f"📍 Beacon {minor_id}: RSSI {rssi} dBm", end="")
    
    # =========================================================
    # SAFE ZONE: RSSI > -80 dBm (Strong Signal = Beacon Nearby)
    # =========================================================
    if rssi > ProximityConfig.RSSI_THRESHOLD:
        print(f" → 🟢 SAFE ZONE (nearby)")
        
        # Stop alarm when beacon returns to safe zone
        if state.alarm_active:
            print(f"   ✅ Beacon returned to safe zone - Stopping alarm")
            stop_alarm(mqtt_client, ProximityConfig.MACRO_SENSOR_EUI, minor_id)
            state.alarm_active = False
        
        state.zone = SecurityZone.SAFE
        state.weak_start = None
        return "SAFE"
    
    # =========================================================
    # ALARM ZONE: RSSI ≤ -80 dBm (Weak Signal = Beacon Far Away)
    # =========================================================
    else:
        # Start debounce timer
        if state.weak_start is None:
            state.weak_start = time.time()
            state.zone = SecurityZone.WEAK
            print(f" → 🟡 WEAK SIGNAL - monitoring...")
            return "WEAK"
        
        weak_duration = time.time() - state.weak_start
        
        # If weak for long enough, trigger alarm
        if weak_duration >= ProximityConfig.DEBOUNCE_SECONDS:
            print(f" → 🔴 ALARM ZONE (weak for {weak_duration:.1f}s)")
            
            if not state.alarm_active:
                print(f"\n🚨 ═══════════════════════════════════════════")
                print(f"🚨  ALERT: Beacon leaving safe zone!")
                print(f"🚨  Beacon: {minor_id}")
                print(f"🚨  RSSI: {rssi} dBm (threshold: {ProximityConfig.RSSI_THRESHOLD})")
                print(f"🚨 ═══════════════════════════════════════════\n")
                
                trigger_alarm_with_sequence(mqtt_client, ProximityConfig.MACRO_SENSOR_EUI, minor_id)
                state.alarm_active = True
            
            state.zone = SecurityZone.ALARM
            return "ALARM"
        else:
            print(f" → 🟡 WEAK ({weak_duration:.1f}s / {ProximityConfig.DEBOUNCE_SECONDS}s)")
            return "WEAK"


def check_floor_security(rssi: int, minor_id: str, mqtt_client: Any) -> SecurityZone:
    result = check_alarm_conditions(rssi, minor_id, mqtt_client)
    return SecurityZone[result]


# =============================================================================
# ALARM TRIGGER - SEND AC SEARCH BEACON COMMAND
# =============================================================================

def trigger_alarm_with_sequence(mqtt_client: Any, sensor_eui: str, beacon_minor: str) -> bool:
    """
    Trigger alarm by sending the AC Search Beacon command.
    
    Command Structure: AC + 00 (MsgID) + [Beacon_Minor_ID]
    Example: If Beacon ID is 64AF, payload is AC0064AF
    
    NOTE: Volume configuration (B0...) removed - configure volume manually once.
    
    Args:
        mqtt_client: MQTT client for publishing downlinks
        sensor_eui: Target sensor's DevEUI
        beacon_minor: Beacon Minor ID (e.g., "64B0", "64AF")
    
    Returns:
        bool: True if command sent successfully
    """
    global _msg_id_counter
    
    # Build trigger command: AC + MsgID + Minor
    # MsgID increments to ensure each command is unique (sensor ignores duplicates)
    msg_id = f"{_msg_id_counter:02X}"
    _msg_id_counter = (_msg_id_counter + 1) % 256
    
    minor = beacon_minor.upper().zfill(4)
    trigger_hex = f"AC{msg_id}{minor}"  # AC + MsgID + Minor
    
    print(f"\n🚨 TRIGGER ALARM: {trigger_hex}")
    print(f"   Target Sensor: {sensor_eui}")
    print(f"   Beacon Minor: {minor}")
    
    success = _send_downlink_to_device(
        mqtt_client, 
        sensor_eui, 
        trigger_hex, 
        f"SEARCH BEACON ({trigger_hex})"
    )
    
    if success:
        print(f"   ✅ Command sent!")
    else:
        print(f"   ❌ Failed to send command!")
    
    return success


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


def _send_downlink_to_device(mqtt_client: Any, device_eui: str, hex_cmd: str, cmd_name: str) -> bool:
    """
    Send a downlink command to a specific device.
    
    Args:
        mqtt_client: MQTT client
        device_eui: Target device's DevEUI
        hex_cmd: Hex command string (e.g., "B0000103")
        cmd_name: Human-readable command name for logging
    
    Returns:
        bool: True if published successfully
    """
    global _app_id
    
    # Use the hardcoded Macro Sensor App ID (not the dynamic one from uplinks!)
    app_id = ProximityConfig.MACRO_SENSOR_APP_ID
    
    try:
        topic = f"application/{app_id}/device/{ProximityConfig.MACRO_SENSOR_EUI}/command/down"
        
        data_bytes = bytes.fromhex(hex_cmd)
        data_b64 = base64.b64encode(data_bytes).decode('utf-8')
        
        payload = {
            "devEui": ProximityConfig.MACRO_SENSOR_EUI,
            "confirmed": False,
            "fPort": ProximityConfig.FPORT,
            "data": data_b64
        }
        
        # DEBUG: Print full details
        print(f"   📡 {cmd_name}: {hex_cmd} → FPort {ProximityConfig.FPORT}")
        print(f"   📝 Topic: {topic}")
        print(f"   📝 App ID (HARDCODED): {app_id}")
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
