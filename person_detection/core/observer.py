"""
Observer Pattern Implementation for Person Detection Microservice
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Protocol
from enum import Enum


class EventType(Enum):
    """Event types for the observer pattern"""
    SESSION_STARTED = "session_started"
    SESSION_CLOSED = "session_closed"
    PERSON_DETECTED = "person_detected"
    FRAME_PROCESSED = "frame_processed"
    ERROR_OCCURRED = "error_occurred"


class Event:
    """Event class to pass data to observers"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = data.get("timestamp")


class Observer(ABC):
    """Abstract observer interface"""
    
    @abstractmethod
    def update(self, event: Event):
        """Update method called when event occurs"""
        pass


class Subject:
    """Subject class that maintains a list of observers"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer):
        """Attach an observer"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        """Detach an observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event: Event):
        """Notify all observers of an event"""
        for observer in self._observers:
            observer.update(event)


class SessionObserver(Observer):
    """Observer for session events"""
    
    def update(self, event: Event):
        if event.event_type in [EventType.SESSION_STARTED, EventType.SESSION_CLOSED]:
            print(f"Session event: {event.event_type.value} - {event.data}")


class DetectionObserver(Observer):
    """Observer for detection events"""
    
    def update(self, event: Event):
        if event.event_type == EventType.PERSON_DETECTED:
            person_count = len(event.data.get('detections', []))
            print(f"Detection event: {person_count} persons detected")


class LoggingObserver(Observer):
    """Observer for logging events"""
    
    def update(self, event: Event):
        print(f"Log: [{event.event_type.value}] {event.data}")


class EventManager(Subject):
    """Event manager to handle all events in the system"""
    
    def __init__(self):
        super().__init__()
        self._event_history: List[Event] = []
    
    def emit(self, event_type: EventType, data: Dict[str, Any]):
        """Emit an event to all observers"""
        event = Event(event_type, data)
        self._event_history.append(event)
        self.notify(event)
    
    def get_event_history(self) -> List[Event]:
        """Get history of all events"""
        return self._event_history.copy()
    
    def clear_event_history(self):
        """Clear event history"""
        self._event_history.clear()