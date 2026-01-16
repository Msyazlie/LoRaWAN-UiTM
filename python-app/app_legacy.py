import paho.mqtt.client as mqtt
import json
import os
import sys
import time
import struct
import threading

# --- CONFIGURATION ---
BROKER_ADDRESS = os.getenv('MQTT_BROKER', '127.0.0.1')
BROKER_PORT = 1883
TOPIC = "application/+/device/+/event/up"

# --- SCENARIO: LEASH / ANTI-THEFT ---
# "Trigger alarm if beacon moves to other floor (moves away)"

# 1. TRACKED BEACON
TRACKED_BEACON_ID = "001064b0" 

# 2. DEVICES IN SAFE ZONE (Floor 1)
# These devices monitor the beacon.
# If they see the beacon with STRONG signal -> Safe.
# If they see the beacon with WEAK signal -> Leaving Floor -> Alarm.
SCANNERS = {
    "70b3d5a4d31205cf": "Macro Sensor (Safe Zone)",
    "70b3d5a4d3120591": "Gateway (Safe Zone)"
}

# 3. ALARM TRIGGER DEVICE
# Which device should ring the alarm? (The Macro Sensor)
ALARM_TMACRO_SENSOR_EUI = "70b3d5a4d31205cf"

# 4. THRESHOLD SETTINGS
# If RSSI is lower than this (e.g. -90), assume it's moving to another floor.
SAFE_RSSI_THRESHOLD = -85 

# ALARM COMMAND
ALARM_PAYLOAD_HEX = "01" 
ALARM_FPORT = 2

# --- GLOBAL STATE (For Real-Time Dashboard) ---
last_beacon_stats = {
    "seen": False,
    "rssi": 0,
    "sensor": "",
    "time": 0,
    "id": ""
}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
        print(f"   👀 Watching for Beacon [{TRACKED_BEACON_ID}]...")
        print(f"   🏙️  Safe Zone Scanners: {list(SCANNERS.keys())}")
        print(f"   🚨 Alarm Target: {ALARM_TARGET_EUI}")
        print(f"   📏 Safe Radius Limit: > {SAFE_RSSI_THRESHOLD} dBm")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def decode_lansitec_hex(hex_string):
    """
    Decodes the raw Hex string from Lansitec Macro Sensor.
    Example: d001001064b0c4
    """
    try:
        # Convert hex string to bytes
        data_bytes = bytes.fromhex(hex_string)
        
        # Basic Validation (Length must be at least 7 bytes for 1 beacon)
        if len(data_bytes) < 7:
            return None

        # Extract the Beacon ID (Bytes 2,3,4,5)
        # 001064b0
        beacon_id_bytes = data_bytes[2:6]
        beacon_id = beacon_id_bytes.hex()

        # Extract RSSI (Last Byte)
        # c4 -> 196.  196 - 256 = -60dBm
        rssi_byte = data_bytes[-1]
        rssi = rssi_byte - 256 if rssi_byte > 127 else rssi_byte

        return {"id": beacon_id, "rssi": rssi}
    except Exception as e:
        print(f"   ⚠️ Decoder Error: {e}")
        return None

def send_downlink(client, application_id, dev_eui, data_hex):
    """
    Sends a downlink command to a device via ChirpStack MQTT.
    """
    topic = f"application/{application_id}/device/{dev_eui}/command/down"
    
    # Convert Hex to Base64
    try:
        data_bytes = bytes.fromhex(data_hex)
        import base64
        data_b64 = base64.b64encode(data_bytes).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding downlink data: {e}")
        return

    payload = {
        "devEui": dev_eui,
        "confirmed": False,
        "fPort": ALARM_FPORT,
        "data": data_b64
    }
    
    try:
        client.publish(topic, json.dumps(payload))
        print(f"   🚀 ALARM ACTIVATED! Downlink sent to {dev_eui}")
    except Exception as e:
        print(f"❌ Failed to publish downlink: {e}")

def trigger_alarm(client, app_id):
    print("\n" + "="*40)
    print("🚨🚨 ALARM TRIGGERED! 🚨🚨")
    print(f"   BEACON MOVING AWAY (LEAVING SAFE ZONE)")
    print("="*40 + "\n")
    
    # SEND COMMAND TO DEVICE
    send_downlink(client, app_id, ALARM_TARGET_EUI, ALARM_PAYLOAD_HEX)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # 1. Get the Sender DevEUI
        if 'deviceInfo' in payload:
            sensor_eui = payload['deviceInfo'].get('devEui')
            app_id = payload['deviceInfo'].get('applicationId')
        else:
            return

        # =========================================================
        # STRATEGY 1: Check if ChirpStack ALREADY decoded it (JS Codec)
        # =========================================================
        decoded_beacons = []
        
        if 'object' in payload:
            obj = payload['object']
            for key, val in obj.items():
                if key.startswith("beacon"):
                    idx = key.replace("beacon", "") 
                    rssi_str = obj.get(f"rssi{idx}", "-999dBm")
                    try:
                        rssi_val = int(str(rssi_str).replace("dBm", "").split(".")[0])
                    except:
                        rssi_val = -999
                    decoded_beacons.append({"id": val, "rssi": rssi_val})

        # =========================================================
        # STRATEGY 2: If not decoded, try RAW HEX (Manual Decode)
        # =========================================================
        if not decoded_beacons:
            raw_hex = ""
            if 'object' in payload and 'raw' in payload['object']:
                raw_hex = payload['object']['raw']
            elif 'data' in payload:
                import base64
                raw_hex = base64.b64decode(payload['data']).hex()
            
            if raw_hex:
                beacon_data = decode_lansitec_hex(raw_hex)
                if beacon_data:
                    decoded_beacons.append(beacon_data)

        # =========================================================
        # PROCESS DETECTED BEACONS
        # =========================================================
        for beacon in decoded_beacons:
            detected_id = beacon['id']
            rssi = beacon['rssi']
            
            # Normalize casing for comparison
            if str(detected_id).upper() == TRACKED_BEACON_ID.upper():
                
                # --- UPDATE DASHBOARD STATS ---
                last_beacon_stats["seen"] = True
                last_beacon_stats["rssi"] = rssi
                last_beacon_stats["sensor"] = sensor_eui
                last_beacon_stats["time"] = time.time()
                last_beacon_stats["id"] = detected_id

                # NEW LOGIC: LEASH MODE
                # Check RSSI Strength
                # -85 is stronger than -90. 
                # If RSSI (-95) < THRESHOLD (-85) -> TOO WEAK (FAR)
                
                is_safe = rssi >= SAFE_RSSI_THRESHOLD
                
                status_icon = "✅" if is_safe else "⚠️"
                status_msg = "SAFE (Nearby)" if is_safe else "WARNING (Moving Away!)"
                
                print(f"\r[{time.strftime('%H:%M:%S')}] {status_icon} Signal: {rssi} dBm | {status_msg} | Scanner: {sensor_eui[-4:]}")

                if not is_safe:
                    trigger_alarm(client, app_id)

                
    except Exception as e:
        print(f"⚠️ Error: {e}")

# --- BACKGROUND THREAD FOR "HEARTBEAT" ---
def print_status_loop():
    """
    Prints a status update every second.
    """
    while True:
        # Dynamic Dashboard Line
        if last_beacon_stats["seen"]:
            diff = int(time.time() - last_beacon_stats["time"])
            s_id = last_beacon_stats["sensor"][-4:] # Last 4 chars for brevity
            rssi = last_beacon_stats['rssi']
            
            # Show "Leaving?" hint in dashboard
            status = "safe" if rssi >= SAFE_RSSI_THRESHOLD else "LEAVING!"
            
            msg = f"Last: {rssi} dBm ({status}) ...{s_id} ({diff}s ago)"
        else:
            msg = "Searching for Signal..."

        sys.stdout.write(f"\r[{time.strftime('%H:%M:%S')}] ⏳ {msg}       ")
        sys.stdout.flush()
        time.sleep(1)

# --- MAIN ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Start logic
try:
    client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("🚀 System Running...")
    
    # Enable the background heartbeat
    t = threading.Thread(target=print_status_loop, daemon=True)
    t.start()
    
    client.loop_forever()
    
except Exception as e:
    print(f"System Error: {e}")