import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\msyaz\Desktop\TH IOT\UiTM\python-app")

import beacon_logic
import settings

# Mock Settings if needed, but we can rely on settings.py
print(f"Targeting Beacon ID (Major): {settings.TARGET_MAJOR_VALUE}")
print(f"Targeting Beacon ID (Tracked): {settings.TRACKED_BEACON_ID}")

# Test Case 1: Gateway Payload with DeviceType1 (Standard match)
payload_1 = {
    "beacon1": "001064B0",
    "rssi1": -95,
    "beacon1_minor": "1234", # Irrelevant if Major matches
    "type": "DeviceType1"
}

# Test Case 2: Gateway Payload with Minor Match (Alternative)
payload_2 = {
    "beacon1": "FFFFFFFF", # No match
    "rssi1": -50,
    "beacon1_minor": settings.TARGET_MAJOR_VALUE, # MATCH! "0010"
    "rssi1": -100, # Weak signal
    "type": "DeviceType1"
}

# Test Case 3: No Match
payload_3 = {
    "beacon1": "AABBCCDD",
    "rssi1": -80,
    "type": "DeviceType1"
}

print("\n--- Running Tests ---")

result1 = beacon_logic.decode_gateway_json(payload_1)
print(f"Test 1 (Direct Major Match): {result1}")
if result1 and result1['id'] == "001064B0" and result1['rssi'] == -95:
    print("✅ Test 1 Passed")
else:
    print("❌ Test 1 Failed")

result2 = beacon_logic.decode_gateway_json(payload_2)
print(f"Test 2 (Minor Match): {result2}")
# Note: In the code we prioritize full match, then minor match.
# In payload 2, minor matches '0010'. 
# logic: beacon_val = payload['beacon1'] -> "FFFFFFFF" (Not match)
#        minor_val = payload['beacon1_minor'] -> "0010" (Settings.TARGET_MAJOR_VALUE) -> MATCH
# Function returns {'id': beacon_val, 'rssi': ...} -> ID will be FFFFFFFF strictly speaking based on current logic?
# Let's check logic: return {"id": beacon_val, ...}
# Yes, it returns the Beacon ID found in the slot, even if matched by Minor. This is acceptable.
if result2 and result2['rssi'] == -100:
    print("✅ Test 2 Passed")
else:
    print("❌ Test 2 Failed")

result3 = beacon_logic.decode_gateway_json(payload_3)
print(f"Test 3 (No Match): {result3}")
if result3 is None:
    print("✅ Test 3 Passed")
else:
    print("❌ Test 3 Failed")
