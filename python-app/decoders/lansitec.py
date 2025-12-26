import struct

def decode_lansitec_gateway(payload_hex):
    """
    Decodes payload from Lansitec Bluetooth Gateway.
    Format is often Type-Length-Value or specific struct based on configuration.
    
    Assuming standard format:
    Byte 0: Report Type (0x01 = Beacon report)
    Byte 1: Beacon Type (0x00 = iBeacon, 0x01 = Eddystone)
    Byte 2: RSSI (signed)
    Byte 3-N: Beacon Data
    
    iBeacon Data (Length 21 chars typically if raw, or parsed):
    UUID (16 bytes)
    Major (2 bytes)
    Minor (2 bytes)
    TxPower (1 byte)
    """
    try:
        data = bytes.fromhex(payload_hex)
        
        # This is a simplified decoder based on common Lansitec behaviors.
        # Actual format depends heavily on Gateway Config (register settings).
        
        results = {}
        
        if len(data) < 5:
            return {"error": "Payload too short", "raw": payload_hex}

        report_type = data[0]
        
        if report_type in [0x01, 0x02]: # Beacon Report
            # Structure might be: [ReportType][BeaconType][RSSI][Addr][Data...]
            # Let's try to extract typical iBeacon fields
            
            # Simple heuristic: Look for valid UUID pattern if position is variable
            # or try fixed result.
            
            # Assuming Fixed Format for iBeacon:
            # 0: Report Type
            # 1-6: MAC Address (sometimes reversed)
            # 7: RSSI
            # 8-23: UUID
            # 24-25: Major
            # 26-27: Minor
            # 28: TxPower
            # 29: Battery (optional)
            
            # Let's support a generic binary parsing if we don't have exact Register map.
            
            offset = 0
            results['type'] = 'beacon_report'
            results['report_type_id'] = report_type
            
            # Fake parsing based on typical length of iBeacon report in Lansitec
            if len(data) >= 25: 
                 # This is likely containing the full UUID
                 # Let's assume the payload IS the beacon advertisement data directly forwarded
                 pass

        return {"raw": payload_hex, "note": "Decoder implementaton is generic. Needs real sample to refine."}

    except Exception as e:
        return {"error": str(e), "raw": payload_hex}


def decode_b002_beacon(payload_hex):
    """
    Decodes the raw BLE Ad Data if available.
    Lansitec B002 sends iBeacon info.
    """
    # iBeacon defined structure:
    # Prefix: 02 01 06 1A FF 4C 00 02 15
    # UUID: 16 bytes
    # Major: 2 bytes
    # Minor: 2 bytes
    # TxPower: 1 byte
    
    try:
        data = bytes.fromhex(payload_hex)
        hex_str = payload_hex.upper()
        
        # Look for iBeacon prefix
        ibeacon_prefix = "0215" # Apple ID follow 4C00
        
        idx = hex_str.find(ibeacon_prefix)
        if idx != -1:
             # Aligned generic
             pass
             
        # Just return raw for now as we need to see how Gateway wraps it
        return {"raw_beacon_payload": payload_hex}
    except:
        return {}
