import os
import json

# --- MQTT CONNECTION ---
BROKER_ADDRESS = os.getenv('MQTT_BROKER', '127.0.0.1')
BROKER_PORT = 1883
TOPIC = "application/+/device/+/event/up"

# --- BEACON WATCHLIST ---
# List of beacon Minor IDs to track (matched against payload data)
TARGET_BEACONS = ["64B0", "64AF", "64AE"]  # Default fallback if beacons.json not found

# Auto-discovery: Automatically add new beacons to watchlist at runtime
AUTO_DISCOVER_BEACONS = False

# External watchlist file path
WATCHLIST_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "beacons.json")

# Legacy single-beacon ID (for backward compatibility)
TRACKED_BEACON_ID = "0010"
TARGET_SERVICE_UUID = "fff6"   # BLE UUID to look for

# --- SCANNERS & CLOUD ---
# Map DevEUIs to Human Readable Names
SCANNERS = {
    "70b3d5a4d31205cf": "Macro Sensor (Safe Zone)",
    "70b3d5a4d3120591": "Gateway (Safe Zone)"
}

# --- ALARM SETTINGS ---
ALARM_TARGET_EUI = "70b3d5a4d31205cf"  # Device that rings
ALARM_FPORT = 10  # FPort for Lansitec management/config commands (Standard port)

# Downlink Commands
ALARM_CMD_HEX = "AC"            # Base trigger command (appended with MSGID + MINOR)
ALARM_OFF_HEX = "B0000100"      # SILENCE COMMAND (Mute Buzzer: Type B0, Vol 00)
ALARM_VOL_HIGH_HEX = "B0000103" # UNMUTE COMMAND (Set Vol 3 - High)

# --- THRESHOLDS ---
SAFE_RSSI_THRESHOLD = -80   # dBm - Above this = Safe Zone (Same Floor)
ALARM_RSSI_THRESHOLD = -85  # dBm - Below this = Alarm Zone (Other Floor)
DEBOUNCE_SECONDS = 5        # Sustain weak signal for X seconds before alarm
MAX_SILENCE_DURATION = 120  # Watchdog: Seconds of no signal before alarm
GUI_TIMEOUT_SECONDS = 120   # GUI: Grace period to keep "Safe Zone" on screen


# --- WATCHLIST LOADER ---
def load_watchlist():
    """
    Loads beacon watchlist from beacons.json if exists, otherwise uses TARGET_BEACONS.
    
    Returns:
        dict: {beacon_id: {"name": "...", "id": "..."}, ...}
    """
    watchlist = {}
    
    # Try external JSON file first
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                data = json.load(f)
                for beacon in data.get("beacons", []):
                    bid = beacon.get("id", "").upper()
                    if bid:
                        watchlist[bid] = {
                            "id": bid,
                            "name": beacon.get("name", f"Beacon {bid}")
                        }
            if watchlist:
                print(f"📋 Loaded {len(watchlist)} beacons from {WATCHLIST_FILE}")
                return watchlist
        except Exception as e:
            print(f"⚠️ Failed to load {WATCHLIST_FILE}: {e}")
    
    # Fallback to TARGET_BEACONS list
    for bid in TARGET_BEACONS:
        bid_upper = bid.upper()
        watchlist[bid_upper] = {
            "id": bid_upper,
            "name": f"Beacon {bid_upper}"
        }
    
    print(f"📋 Using {len(watchlist)} beacons from TARGET_BEACONS setting")
    return watchlist
