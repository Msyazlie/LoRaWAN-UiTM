"""
Event Manager Service

A simple observer pattern implementation to decouple logic from custom actions.
This allows different parts of the system to subscribe to events without
tight coupling.
"""

from typing import Callable, Dict, List, Any
import logging

# Configure basic logging if not already configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventManager:
    _instance = None
    _subscribers: Dict[str, List[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._subscribers = {}
        return cls._instance

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable):
        """
        Subscribe to an event.
        
        Args:
            event_name: The name of the event to listen for.
            callback: The function to call when the event is emitted.
                      Should accept a single argument (the data payload).
        """
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        cls._subscribers[event_name].append(callback)
        logger.info(f"Subscribed to event: {event_name}")

    @classmethod
    def emit(cls, event_name: str, data: Any = None):
        """
        Emit an event to all subscribers.
        
        Args:
            event_name: The name of the event to emit.
            data: Optional data payload to pass to subscribers.
        """
        if event_name in cls._subscribers:
            for callback in cls._subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_name}: {e}")
