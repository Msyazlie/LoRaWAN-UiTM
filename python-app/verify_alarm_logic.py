import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.logic import alarm_rules
from src.config import settings
from src.hooks import custom_actions

# Register hooks to test dashboard integration
custom_actions.register_hooks()

# Mock MQTT Client
class MockMQTT:
    def publish(self, topic, payload):
        # print(f"[MOCK MQTT] Published to {topic}: {payload}")
        pass

mock_mqtt = MockMQTT()

# Configuration from devices.json (Verified via file view)
# Level 1 Gateway: 70b3d5a4d31205c5
# Level G Gateway: 70b3d5a4d31205c4
# Beacon 64AF Home: Level 1
# Beacon 64B0 Home: Level G

GATEWAY_LEVEL_1 = "70b3d5a4d31205c5"
GATEWAY_LEVEL_G = "70b3d5a4d31205c4"
BEACON_LEVEL_1 = "64AF"

print("="*60)
print("VERIFYING ALARM LOGIC")
print(f"Beacon: {BEACON_LEVEL_1} (Home: Level 1)")
print(f"RSSI Threshold: {settings.SAFE_RSSI_THRESHOLD} dBm")
print("="*60)

# Pre-initialize beacon state to SAFE so 'old_zone' is not None -> triggers event on change
state = alarm_rules.get_beacon_state(BEACON_LEVEL_1)
state.zone = alarm_rules.SecurityZone.SAFE
print("Initialized Beacon State to SAFE")
print("="*60)

test_cases = [
    {
        "name": "Startup Silence Check (Uninitialized State)",
        "rssi": -90, # Weak Signal (Would be ALARM normally)
        "gateway": GATEWAY_LEVEL_G, # Wrong Floor (Would be ALARM normally)
        "expected": "SAFE", # EXPECT SILENCE ON STARTUP
        "desc": "First detection must be silent",
        "force_reset": True 
    },
    {
        "name": "Wrong Floor, Strong Signal (-50)",
        "rssi": -50,
        "gateway": GATEWAY_LEVEL_G, # Level G (Wrong)
        "expected": "ALARM",
        "desc": "Wrong location"
    },
    {
        "name": "Wrong Floor, Weak Signal (-90)",
        "rssi": -90,
        "gateway": GATEWAY_LEVEL_G, # Level G (Wrong)
        "expected": "ALARM",
        "desc": "Wrong location"
    },
    {
        "name": "Right Floor, Weak Signal (-90)",
        "rssi": -90,
        "gateway": GATEWAY_LEVEL_1, # Level 1 (Right)
        "expected": "ALARM",
        "desc": "Too far away"
    },
    {
        "name": "Right Floor, Strong Signal (-60)",
        "rssi": -60,
        "gateway": GATEWAY_LEVEL_1, # Level 1 (Right)
        "expected": "SAFE",
        "desc": "Correct location & range"
    },
    {
        "name": "Right Floor, Very Strong Signal (-50)",
        "rssi": -50,
        "gateway": GATEWAY_LEVEL_1, # Level 1 (Right)
        "expected": "SAFE",
        "desc": "Correct location & range (Sanity Check)"
    }
]

passed_count = 0
for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test['name']}")
    print(f"   Input: RSSI {test['rssi']}, Gateway {test['gateway']}")
    
    # Reset state if needed for test
    if test.get("force_reset"):
        state_reset = alarm_rules.get_beacon_state(BEACON_LEVEL_1)
        state_reset.initialized = False
        print(f"   🔄 Forcing State Reset (Initialized=False)")

    result = alarm_rules.check_alarm_conditions(
        rssi=test['rssi'], 
        minor_id=BEACON_LEVEL_1, 
        mqtt_client=mock_mqtt, 
        gateway_eui=test['gateway']
    )
    
    print(f"   Result: {result}")
    
    if result == test['expected']:
        print(f"   ✅ PASSED (Expected {test['expected']})")
        passed_count += 1
    else:
        print(f"   ❌ FAILED (Expected {test['expected']}, Got {result})")

print("\n" + "="*60)
if passed_count == len(test_cases):
    print("🎉 ALL TESTS PASSED")
else:
    print(f"⚠️ {len(test_cases) - passed_count} TESTS FAILED")
print("="*60)
