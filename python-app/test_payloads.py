import json
import base64
from decoders.lansitec import decode_lansitec_gateway

def test_decoders():
    print("Testing Lansitec Decoder...")
    
    # Test Case 1: Hypothetical Beacon Report
    # Type 01, BeaconType 00 (iBeacon), RSSI -70 (BA), ... Data
    fake_hex = "0100BA00112233445566778899AABBCCDDEEFF"
    result = decode_lansitec_gateway(fake_hex)
    print(f"Input: {fake_hex}")
    print(f"Output: {result}")
    
    print("\nTesting Base64 Conversion logic...")
    # Simulate Chirpstack Base64
    fake_base64 = base64.b64encode(bytes.fromhex(fake_hex)).decode('utf-8')
    print(f"Base64: {fake_base64}")
    
    decoded_bytes = base64.b64decode(fake_base64)
    decoded_hex = decoded_bytes.hex()
    print(f"Recovered Hex: {decoded_hex}")
    
    assert decoded_hex.upper() == fake_hex.upper()
    print("✅ Base64 logic matches.")

if __name__ == "__main__":
    test_decoders()
