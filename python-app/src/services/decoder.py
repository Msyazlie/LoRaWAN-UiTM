import base64
from src.config import settings

# Global watchlist (loaded at module import)
_watchlist = None

def get_watchlist():
    """Returns the current watchlist, loading it if needed."""
    global _watchlist
    if _watchlist is None:
        _watchlist = settings.load_watchlist()
    return _watchlist

def reload_watchlist():
    """Forces a reload of the watchlist from file."""
    global _watchlist
    _watchlist = settings.load_watchlist()
    return _watchlist

def is_beacon_tracked(beacon_id):
    """
    Checks if a beacon ID is in the watchlist.
    Matches if the beacon_id contains any tracked ID.
    
    Returns:
        tuple: (is_tracked: bool, matched_id: str or None)
    """
    watchlist = get_watchlist()
    beacon_upper = str(beacon_id).upper()
    
    for tracked_id in watchlist.keys():
        if tracked_id in beacon_upper:
            return True, tracked_id
    return False, None

def extract_minor_id(full_beacon_id):
    """
    Extracts the Minor ID from a full beacon ID string.
    Beacon IDs are typically Major+Minor (e.g., "001064AF" -> Minor is "64AF")
    """
    full_id = str(full_beacon_id).upper()
    if len(full_id) >= 4:
        return full_id[-4:]  # Last 4 hex chars = 2 bytes = Minor
    return full_id

def decode_gateway_json(payload_object, filter_tracked=True):
    """
    Parses the DECODED object from the Bluetooth Gateway (ChirpStack).
    
    Gateway sends:
    {
        "type": "DeviceType1",
        "number": 2,
        "beacon1": "001064AF",
        "rssi1": -42,
        "beacon2": "001064B0",
        "rssi2": -88
    }
    
    Args:
        payload_object: The decoded JSON object from ChirpStack
        filter_tracked: If True, only return beacons in watchlist
    
    Returns:
        List of dicts: [{"id": "...", "minor": "...", "rssi": -XX, "tracked": bool}, ...]
    """
    try:
        all_beacons = []
        watchlist = get_watchlist()
        
        # Loop through beacon slots (beacon1, beacon2, etc.)
        for i in range(1, 11):
            beacon_key = f"beacon{i}"
            rssi_key = f"rssi{i}"
            
            if beacon_key in payload_object:
                beacon_val = str(payload_object[beacon_key]).upper()
                rssi = int(payload_object.get(rssi_key, -999))
                
                # Extract minor ID (last 4 hex chars)
                minor_id = extract_minor_id(beacon_val)
                
                # Check if tracked
                is_tracked, matched_id = is_beacon_tracked(beacon_val)
                
                # Get name from watchlist
                name = watchlist.get(matched_id, {}).get("name", f"Beacon {minor_id}") if matched_id else f"Beacon {minor_id}"
                
                beacon_data = {
                    "id": beacon_val,
                    "minor": minor_id,
                    "rssi": rssi,
                    "tracked": is_tracked,
                    "matched_id": matched_id,
                    "name": name
                }
                
                # Auto-discovery
                if not is_tracked and settings.AUTO_DISCOVER_BEACONS:
                    watchlist[minor_id] = {
                        "id": minor_id,
                        "name": f"Auto-Discovered {minor_id}"
                    }
                    beacon_data["tracked"] = True
                    beacon_data["matched_id"] = minor_id
                    print(f"🆕 Auto-discovered beacon: {minor_id}")
                
                if filter_tracked:
                    if beacon_data["tracked"]:
                        all_beacons.append(beacon_data)
                else:
                    all_beacons.append(beacon_data)
        
        return all_beacons if all_beacons else None
        
    except Exception as e:
        print(f"Gateway Decode Error: {e}")
        return None

def decode_uplink(payload, filter_tracked=True):
    """
    Main Entry Point to Decode an MQTT Uplink Payload.
    
    Args:
        payload: MQTT payload dict from ChirpStack
        filter_tracked: If True, only return tracked beacons
    
    Returns:
        List of beacon dicts or None
    """
    try:
        # Try Gateway JSON Object (if pre-decoded by ChirpStack JS decoder)
        if 'object' in payload:
            res = decode_gateway_json(payload['object'], filter_tracked)
            if res: 
                return res

        # Fallback: Extract Raw Hex and try to decode
        raw_hex = ""
        if 'data' in payload:
            raw_hex = base64.b64decode(payload['data']).hex()
        
        if not raw_hex: 
            return None

        # For raw hex, we'd need device-specific decoding
        # This is a simplified version
        return None

    except Exception as e:
        print(f"Decode Error: {e}")
        return None
