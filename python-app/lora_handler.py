import json
import base64
import settings

def send_downlink(client, app_id, dev_eui, hex_cmd):
    """
    Sends a downlink command to a device via ChirpStack MQTT.
    hex_cmd: "01" (Alarm) or "00" (Silence)
    """
    topic = f"application/{app_id}/device/{dev_eui}/command/down"
    
    try:
        data_bytes = bytes.fromhex(hex_cmd)
        data_b64 = base64.b64encode(data_bytes).decode('utf-8')
    except Exception as e:
        print(f"❌ Encoding Error: {e}")
        return False

    payload = {
        "devEui": dev_eui,
        "confirmed": False,
        "fPort": settings.ALARM_FPORT,
        "data": data_b64
    }
    
    try:
        client.publish(topic, json.dumps(payload))
        return True
    except Exception as e:
        print(f"❌ Publish Error: {e}")
        return False

def trigger_alarm(client, app_id):
    print("\n" + "="*40)
    print("🚨🚨 ALARM TRIGGERED! (Leaving Safe Zone) 🚨🚨")
    print("="*40 + "\n")
    send_downlink(client, app_id, settings.ALARM_TARGET_EUI, settings.ALARM_ON_HEX)

def silence_alarm(client, app_id):
    print("\n" + "="*40)
    print("✅ SIGNAL RESTORED - SILENCING ALARM")
    print("="*40 + "\n")
    send_downlink(client, app_id, settings.ALARM_TARGET_EUI, settings.ALARM_OFF_HEX)
