"""
Proximity Alarm System - Main Application

Monitors beacons via Bluetooth Gateway and triggers alarms.
GUI updates in real-time from MQTT data stream.
"""

import tkinter as tk
import time
import threading
from src.config import settings
from src.services.mqtt_client import MQTTClient
from src.services.decoder import decode_uplink, get_watchlist
from src.logic.alarm_rules import (
    check_alarm_conditions, 
    set_app_id, 
    get_all_beacon_states,
    ProximityConfig
)
from src.ui.monitor_window import MonitorWindow


# =============================================================================
# GLOBAL STATE
# =============================================================================

current_app_id = None
gui_root = None
window = None
mqtt_svc = None


# =============================================================================
# MQTT MESSAGE HANDLER (Thread-Safe)
# =============================================================================

def on_mqtt_message(payload):
    """
    Callback when MQTT uplink message is received.
    
    THIS RUNS ON MQTT BACKGROUND THREAD!
    Use gui_root.after() for thread-safe GUI updates.
    
    JSON Format from Gateway:
    {
        "object": {
            "type": "DeviceType1",
            "number": 2,
            "beacon1": "001064AF",
            "rssi1": -42,
            "beacon2": "001064B0",
            "rssi2": -88
        }
    }
    """
    global current_app_id
    
    # 1. Capture Application ID for downlinks
    if 'deviceInfo' in payload:
        new_app_id = payload['deviceInfo']['applicationId']
        
        # Update Application ID if it changes
        if current_app_id != new_app_id:
            current_app_id = new_app_id
            set_app_id(new_app_id)

    # 2. Decode beacon data from gateway JSON
    beacons = decode_uplink(payload, filter_tracked=True)
    
    if beacons:
        # 3. Process each tracked beacon through alarm logic
        for beacon in beacons:
            minor_id = beacon.get("matched_id") or beacon.get("minor")
            rssi = beacon.get("rssi", -999)
            
            if minor_id and rssi > -999:
                # Check alarm conditions (triggers/silences as needed)
                check_alarm_conditions(rssi, minor_id, mqtt_svc)
        
        # 4. THREAD-SAFE GUI UPDATE using .after()
        # This schedules the update on the main Tkinter thread
        if window and gui_root:
            gui_root.after(0, update_gui_from_states)


def update_gui_from_states():
    """
    Update GUI with current beacon states.
    Called via gui_root.after() for thread safety.
    """
    states = get_all_beacon_states()
    watchlist = get_watchlist()
    
    # Convert to list format expected by GUI
    state_list = []
    for beacon_id, state_data in states.items():
        name = watchlist.get(beacon_id, {}).get("name", f"Beacon {beacon_id}")
        state_list.append({
            "id": beacon_id,
            "name": name,
            "rssi": state_data.get("rssi", 0),
            "state": state_data.get("zone", "UNKNOWN"),
            "last_seen": state_data.get("last_seen", 0)
        })
    
    if window:
        window.update_beacon_states(state_list)


# =============================================================================
# MANUAL CONTROLS
# =============================================================================

def on_manual_alarm():
    """Manual alarm button pressed."""
    from src.logic.alarm_rules import manual_trigger_alarm
    
    print("📢 Manual Alarm Requested")
    if current_app_id:
        watchlist = get_watchlist()
        if watchlist:
            first_beacon = list(watchlist.keys())[0]
            manual_trigger_alarm(mqtt_svc, first_beacon)
    else:
        print("⚠️ Cannot trigger: No App ID (wait for first uplink)")


# =============================================================================
# WATCHDOG LOOP
# =============================================================================

def watchdog_loop():
    """Periodically refresh GUI with current states."""
    while True:
        time.sleep(5)
        if window and gui_root:
            gui_root.after(0, update_gui_from_states)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔔 Proximity Alarm System")
    print("=" * 60)
    print(f"   RSSI Threshold: {ProximityConfig.RSSI_THRESHOLD} dBm")
    print(f"   > {ProximityConfig.RSSI_THRESHOLD} → ALARM (beacon detected)")
    print(f"   ≤ {ProximityConfig.RSSI_THRESHOLD} → SAFE (beacon not detected)")
    print("=" * 60)
    
    # Load beacon watchlist
    watchlist = get_watchlist()
    print(f"\n📋 Tracking {len(watchlist)} beacons:")
    for bid, info in watchlist.items():
        print(f"   • {bid}: {info.get('name', 'Unknown')}")
    print()
    
    # Initialize custom event hooks
    from src.hooks.custom_actions import register_hooks
    register_hooks()

    # Initialize MQTT client
    mqtt_svc = MQTTClient(on_mqtt_message)
    
    # Initialize GUI
    gui_root = tk.Tk()
    window = MonitorWindow(gui_root, on_manual_alarm, None)

    # Connect to MQTT broker
    mqtt_svc.connect()
    
    # Periodically update MQTT status in GUI
    def check_connection():
        window.set_mqtt_connected(mqtt_svc.connected)
        gui_root.after(1000, check_connection)
    
    check_connection()

    # Start watchdog thread
    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()

    print("🎯 System Ready. Monitoring for beacons...")
    print("=" * 60)
    
    # Run GUI main loop (blocking)
    gui_root.mainloop()
