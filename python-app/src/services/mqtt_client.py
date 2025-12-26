import paho.mqtt.client as mqtt
import threading
import json
from src.config import settings

class MQTTClient:
    def __init__(self, on_message_callback):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.on_message_callback = on_message_callback
        self.connected = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            print("Connected to MQTT")
            client.subscribe(settings.TOPIC)
        else:
            print(f"Connection Failed: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.on_message_callback(payload)
        except Exception as e:
            print(f"MQTT Rx Error: {e}")

    def connect(self):
        try:
            print(f"Connecting to MQTT Broker at {settings.BROKER_ADDRESS}:{settings.BROKER_PORT}...")
            self.client.connect(settings.BROKER_ADDRESS, settings.BROKER_PORT, 60)
            # Run loop in background thread
            t = threading.Thread(target=self.client.loop_forever, daemon=True)
            t.start()
        except Exception as e:
            print(f"MQTT Connection Error: {e}")

    def publish(self, topic, payload):
        if self.connected:
            self.client.publish(topic, payload) 
