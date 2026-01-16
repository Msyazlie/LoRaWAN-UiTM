import os

# --- MQTT CONNECTION ---
BROKER_ADDRESS = os.getenv('MQTT_BROKER', 'mosquitto')
BROKER_PORT = 1883
TOPIC = "application/+/device/+/event/up"

BATTERY_UUID = "ff0d"

# --- SCANNERS & CLOUD ---
SCANNERS = {
    "70b3d5a4d31205cf": "Macro Sensor (Safe Zone)",
    "70b3d5a4d3120591": "Gateway (Safe Zone)"
}

# --- ALARM# Default Target Device
DEFAULT_MACRO_SENSOR_EUI = "70b3d5a4d31205cf" # Device that rings
ALARM_FPORT = 2
ALARM_ON_HEX = "01"
ALARM_OFF_HEX = "00"

# --- THRESHOLDS ---
SAFE_RSSI_THRESHOLD = -70  # dBm
DEBOUNCE_SECONDS = 5       # Seconds of weak signal before alarm
MAX_SILENCE_DURATION = 45  # Seconds of no signal before alarm (Different Floor Detection)
