"""
Custom Actions Hooks

This module defines custom functions to be executed when specific events occur.
It subscribes these functions to the EventManager.
"""

from src.services.event_manager import EventManager
import logging

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
    
    print(f"\n[CUSTOM ACTION] Beacon {beacon_id} changed from {old_state} to {new_state} (RSSI: {rssi})")
    
    # You can add more custom logic here, e.g., API calls, external logging, etc.
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
