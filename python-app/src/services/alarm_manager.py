import time
import json
import base64
from src.config import settings
from src.services.decoder import get_watchlist

class BeaconState:
    """
    Tracks the state for a single beacon.
    Each beacon maintains its own SAFE/WEAK/LOST state independently.
    """
    def __init__(self, beacon_id, name=""):
        self.beacon_id = beacon_id
        self.name = name or f"Beacon {beacon_id}"
        self.last_rssi = 0
        self.last_seen = 0
        self.state = "UNKNOWN"  # SAFE, WEAK, LOST, UNKNOWN
        self.weak_signal_start = None
        self.alarm_triggered = False  # Track if we've already triggered for this incident
    
    def to_dict(self):
        """Returns state as dictionary for GUI display."""
        return {
            "id": self.beacon_id,
            "name": self.name,
            "rssi": self.last_rssi,
            "state": self.state,
            "last_seen": self.last_seen,
            "alarm_triggered": self.alarm_triggered
        }


class AlarmManager:
    """
    Manages alarm state for multiple beacons.
    Each beacon is tracked independently with its own state machine.
    """
    
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.beacon_states = {}  # {beacon_id: BeaconState}
        self._msg_id_counter = 0
        
        # Initialize states for all beacons in watchlist
        self._init_beacon_states()
    
    def _init_beacon_states(self):
        """Initialize BeaconState for each beacon in watchlist."""
        watchlist = get_watchlist()
        for beacon_id, info in watchlist.items():
            if beacon_id not in self.beacon_states:
                self.beacon_states[beacon_id] = BeaconState(
                    beacon_id, 
                    info.get("name", f"Beacon {beacon_id}")
                )
        print(f"📊 Tracking {len(self.beacon_states)} beacons")
    
    def get_beacon_state(self, beacon_id):
        """Get or create BeaconState for a beacon ID."""
        if beacon_id not in self.beacon_states:
            watchlist = get_watchlist()
            name = watchlist.get(beacon_id, {}).get("name", f"Beacon {beacon_id}")
            self.beacon_states[beacon_id] = BeaconState(beacon_id, name)
        return self.beacon_states[beacon_id]
    
    def get_all_states(self):
        """Returns all beacon states as list of dicts for GUI."""
        return [state.to_dict() for state in self.beacon_states.values()]
    
    def build_alarm_trigger_cmd(self, beacon_minor_hex=None):
        """
        Builds the complete alarm trigger command.
        Format: AC + MSGID (1 byte) + MINOR_ID (2 bytes)
        """
        minor = beacon_minor_hex or "0000"
        msg_id = f"{self._msg_id_counter:02X}"
        self._msg_id_counter = (self._msg_id_counter + 1) % 256
        minor = minor.upper().zfill(4)
        return f"AC{msg_id}{minor}"

    def process_beacon_data(self, beacons, app_id=None):
        """
        Evaluates a LIST of beacon detections.
        Updates per-beacon states and triggers alarms individually.
        
        Args:
            beacons: List of beacon dicts from decoder
            app_id: ChirpStack application ID for downlinks
        """
        if not beacons: 
            return
        
        # Track which beacons we've seen in this batch
        seen_beacon_ids = set()
        
        for beacon in beacons:
            # Get the matched tracked ID (from watchlist matching)
            matched_id = beacon.get("matched_id") or beacon.get("minor", beacon.get("id"))
            if not matched_id:
                continue
            
            matched_id = matched_id.upper()
            seen_beacon_ids.add(matched_id)
            
            rssi = beacon.get("rssi", -999)
            
            # Get or create state for this beacon
            state = self.get_beacon_state(matched_id)
            state.last_rssi = rssi
            state.last_seen = time.time()
            
            # Evaluate state for this specific beacon
            is_safe = rssi >= settings.SAFE_RSSI_THRESHOLD
            
            if is_safe:
                # TRANSITION TO SAFE
                state.weak_signal_start = None
                
                if state.state != "SAFE":
                    if state.alarm_triggered:
                        self.silence_alarm(app_id, matched_id)
                        state.alarm_triggered = False
                    state.state = "SAFE"
                    print(f"✅ Beacon {matched_id}: SAFE (RSSI {rssi})")
            else:
                # EVALUATE WEAK SIGNAL
                if state.weak_signal_start is None:
                    state.weak_signal_start = time.time()
                    state.state = "WEAK"
                else:
                    duration = time.time() - state.weak_signal_start
                    if duration > settings.DEBOUNCE_SECONDS:
                        if not state.alarm_triggered:
                            self.trigger_alarm(
                                app_id, 
                                reason=f"Beacon {matched_id} left Safe Zone (RSSI {rssi})",
                                beacon_minor=matched_id
                            )
                            state.alarm_triggered = True
                            state.state = "ALARM"
    
    def check_watchdog(self, app_id):
        """
        Called periodically to check if any beacon signal is lost.
        Each beacon is checked independently.
        """
        now = time.time()
        
        for beacon_id, state in self.beacon_states.items():
            if state.last_seen == 0:
                continue  # Never seen yet
            
            diff = now - state.last_seen
            
            if diff > settings.MAX_SILENCE_DURATION:
                if state.state != "LOST":
                    if not state.alarm_triggered:
                        self.trigger_alarm(
                            app_id, 
                            reason=f"Beacon {beacon_id} Signal Lost (Watchdog)",
                            beacon_minor=beacon_id
                        )
                        state.alarm_triggered = True
                    state.state = "LOST"
                    print(f"⚠️ Beacon {beacon_id}: LOST (no signal for {int(diff)}s)")

    def trigger_alarm(self, app_id, reason="Desc", beacon_minor=None):
        """
        Triggers the alarm with proper unmute + dynamic trigger sequence.
        """
        if not app_id: 
            return
        print(f"🚨 TRIGGERING ALARM: {reason}")
        
        # 1. Unmute first
        print(f"   → Step 1: Sending UNMUTE command: {settings.ALARM_VOL_HIGH_HEX}")
        self.send_downlink(app_id, settings.ALARM_VOL_HIGH_HEX)
        time.sleep(1)
        
        # 2. Build & send trigger command
        trigger_cmd = self.build_alarm_trigger_cmd(beacon_minor)
        print(f"   → Step 2: Sending TRIGGER command: {trigger_cmd}")
        self.send_downlink(app_id, trigger_cmd)

    def silence_alarm(self, app_id, beacon_id=None):
        """Silences the alarm (mutes buzzer)."""
        if not app_id: 
            return
        print(f"✅ SILENCING ALARM" + (f" for beacon {beacon_id}" if beacon_id else ""))
        self.send_downlink(app_id, settings.ALARM_OFF_HEX)

    def send_downlink(self, app_id, hex_cmd):
        """Sends a downlink command to the target device via MQTT."""
        topic = f"application/{app_id}/device/{settings.ALARM_TARGET_EUI}/command/down"
        try:
            data_bytes = bytes.fromhex(hex_cmd)
            data_b64 = base64.b64encode(data_bytes).decode('utf-8')
            
            payload = {
                "devEui": settings.ALARM_TARGET_EUI,
                "confirmed": False,
                "fPort": settings.ALARM_FPORT,
                "data": data_b64
            }
            
            print(f"   📡 Downlink → FPort {settings.ALARM_FPORT}, Data: {hex_cmd}")
            self.mqtt_client.publish(topic, json.dumps(payload))
        except Exception as e:
            print(f"❌ Failed to send downlink: {e}")


# --- Standalone Function (for external use) ---

def trigger_alarm_with_unmute(mqtt_client, device_eui, beacon_minor, app_id, fport=None):
    """
    Standalone function to trigger alarm with proper unmute sequence.
    """
    fport = fport or settings.ALARM_FPORT
    topic = f"application/{app_id}/device/{device_eui}/command/down"
    
    def send_cmd(hex_cmd, description):
        try:
            data_bytes = bytes.fromhex(hex_cmd)
            data_b64 = base64.b64encode(data_bytes).decode('utf-8')
            
            payload = {
                "devEui": device_eui,
                "confirmed": False,
                "fPort": fport,
                "data": data_b64
            }
            
            print(f"📡 {description}: {hex_cmd} → FPort {fport}")
            mqtt_client.publish(topic, json.dumps(payload))
            return True
        except Exception as e:
            print(f"❌ Failed to send {description}: {e}")
            return False
    
    print(f"🚨 TRIGGER ALARM WITH UNMUTE → Device: {device_eui}, Beacon: {beacon_minor}")
    
    success1 = send_cmd(settings.ALARM_VOL_HIGH_HEX, "UNMUTE")
    time.sleep(1)
    
    minor = beacon_minor.upper().zfill(4)
    trigger_cmd = f"AC00{minor}"
    success2 = send_cmd(trigger_cmd, "TRIGGER")
    
    return success1 and success2
