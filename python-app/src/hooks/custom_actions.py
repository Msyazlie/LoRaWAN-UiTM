"""
Custom Actions Hooks

This module defines custom functions to be executed when specific events occur.
It subscribes these functions to the EventManager.
"""

import time
import json
import logging
import requests
from src.services.event_manager import EventManager
from src.config.settings import DASHBOARD_WEBHOOK_URL

logger = logging.getLogger(__name__)

def on_beacon_status_change(data):
    """
    Custom function called when a beacon's status changes.
    
    Args:
        data (dict): Data containing beacon ID, old state, and new state.
    """
    beacon_id = data.get('beacon_id')
    old_state = data.get('old_state')
    new_state = data.get('new_state')
    rssi = data.get('rssi')
    timestamp = time.time()
    
    print(f"\n[CUSTOM ACTION] Beacon {beacon_id} changed from {old_state} to {new_state} (RSSI: {rssi})")
    
    # ---------------------------------------------------------
    # DASHBOARD LOGGING (HTTP Webhook)
    # ---------------------------------------------------------
    if DASHBOARD_WEBHOOK_URL:
        try:
            payload = {
                "device_id": beacon_id,
                "status": new_state,
                "rssi": rssi,
                "old_status": old_state,
                "timestamp": int(timestamp * 1000), # Milliseconds
                "location": data.get("location", "Unknown"), # Ensure location is passed in event
                "message": f"Beacon {beacon_id} is now {new_state}"
            }
            
            # Send async or with short timeout to avoid blocking main thread
            # For simplicity in this threaded callback, a short timeout is fine
            response = requests.post(DASHBOARD_WEBHOOK_URL, json=payload, timeout=2)
            
            if response.status_code == 200:
                print(f"[WEBHOOK] ✅ Sent to dashboard: {response.status_code}")
            else:
                print(f"[WEBHOOK] ⚠️ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[WEBHOOK] ❌ Error sending data: {e}")
    else:
        print("[WEBHOOK] ℹ️ skipped (DASHBOARD_WEBHOOK_URL not set)")

    # ---------------------------------------------------------
    # LOCAL ACTIONS
    # ---------------------------------------------------------
    if new_state == 'ALARM':
        print(f"[CUSTOM ACTION] 🚨 CRITICAL ALERT! Initiate emergency protocol for {beacon_id}")
    elif new_state == 'SAFE':
        print(f"[CUSTOM ACTION] ✅ Recovery: {beacon_id} is safe.")

def register_hooks():
    """
    Register all custom hooks with the EventManager.
    """
    EventManager.subscribe("beacon_state_change", on_beacon_status_change)
    logger.info("Custom hooks registered.")
