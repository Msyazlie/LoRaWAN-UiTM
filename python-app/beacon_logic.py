import settings

def decode_ble_packet(raw_hex):
    """
    Parses standard BLE Advertisement Data (Length-Type-Value).
    Looks for 16-bit Service Data (0x16) with specific UUIDs (FFF6, FF0D).
    """
    try:
        data = bytes.fromhex(raw_hex)
        idx = 0
        result = {"id": None, "battery": None}

        while idx < len(data):
            # 1. Read Length
            if idx >= len(data): break
            length = data[idx]
            if length == 0: break 
            
            # 2. Read Type
            if idx + 1 >= len(data): break
            ad_type = data[idx+1]
            
            # 3. Read Content
            chunk = data[idx+2 : idx+1+length]
            
            # CHECK: Service Data (0x16)
            if ad_type == 0x16 and len(chunk) >= 2:
                # First 2 bytes are UUID (Little Endian)
                uuid_bytes = chunk[0:2]
                uuid_hex = uuid_bytes[::-1].hex().lower()
                value_bytes = chunk[2:]
                value_hex = value_bytes.hex()
                
                if uuid_hex == settings.TARGET_SERVICE_UUID:
                    result["id"] = value_hex
                elif uuid_hex == settings.BATTERY_UUID:
                    result["battery"] = value_hex

            # Advance
            idx += (1 + length)
            
        return result if result["id"] else None

    except Exception as e:
        # print(f"BLE Decode Error: {e}") 
        return None

def decode_lansitec_hex(hex_string):
    """
    Decodes the raw Hex string from Lansitec Macro Sensor (Old Format).
    """
    try:
        data_bytes = bytes.fromhex(hex_string)
        if len(data_bytes) < 7: return None

        # Extract Beacon ID (Bytes 2-5)
        beacon_id = data_bytes[2:6].hex()

        # Extract RSSI (Last Byte)
        rssi_byte = data_bytes[-1]
        rssi = rssi_byte - 256 if rssi_byte > 127 else rssi_byte

        return {"id": beacon_id, "rssi": rssi}
    except Exception:
        return None

def decode_gateway_json(payload_object):
    """
    Parses the DECODED object from the Bluetooth Gateway (ChirpStack already ran the JS decoder).
    The JS decoder outputs fields like 'DeviceType1', 'beacon1', 'rssi1', 'DeviceType2', etc.
    We look for our target beacon in those fields.
    """
    try:
        # Determine how many beacons are in the report based on type
        # Or just iterate blindly over possible keys 'beacon1', 'beacon2', etc.
        
        # Check for DeviceType1, DeviceType2, DeviceType3... (Types 8, 9, A)
        # or MultiDeviceTypeMessage (Type E)
        
        # We'll just loop up to a reasonable number (e.g., 5) to find matches
        for i in range(1, 6):
            beacon_key = f"beacon{i}"
            rssi_key = f"rssi{i}"
            minor_key = f"beacon{i}_minor"  # From our modified JS decoder
            
            if beacon_key in payload_object:
                beacon_val = payload_object[beacon_key] # e.g. "001064B0"
                
                # Check Match
                # 1. Match against Full ID (Major+Minor)
                is_match = (beacon_val == settings.TRACKED_BEACON_ID.upper())
                
                # 2. Match against just Minor (if provided in settings or by decoder)
                # The user's JS decoder now outputs `beaconX_minor`
                if not is_match and minor_key in payload_object:
                     minor_val = payload_object[minor_key]
                     if minor_val == settings.TARGET_MAJOR_VALUE: # TARGET_MAJOR_VALUE is actually used as the ID to match in main.py
                         is_match = True
                
                # 3. Match against Settings "Major" (which effectively acts as an ID)
                # Note: valid hex strings are case-insensitive
                if not is_match and settings.TARGET_MAJOR_VALUE and (settings.TARGET_MAJOR_VALUE.upper() in beacon_val):
                    is_match = True

                if is_match:
                    rssi = payload_object.get(rssi_key, -999)
                    return {"id": beacon_val, "rssi": rssi}
                    
        return None
    except Exception as e:
        print(f"Gateway Decode Error: {e}")
        return None
