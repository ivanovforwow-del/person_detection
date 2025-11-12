"""
Session Manager Service for Person Detection Microservice
"""
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .config import settings
from ..core.interfaces import ISessionManager, IDataStorage, IMessageBroker


class SessionManager(ISessionManager):
    """Session management service"""
    
    def __init__(self, storage: IDataStorage, message_broker: IMessageBroker):
        self.storage = storage
        self.message_broker = message_broker
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_info
        self.person_trackers: Dict[str, Dict[str, float]] = {}  # session_id -> {person_id -> last_seen_time}
        self.lock = threading.Lock()
        
        # Start background thread for timeout checks
        self.timeout_checker_thread = threading.Thread(target=self._check_timeouts, daemon=True)
        self.timeout_checker_thread.start()
    
    def start_session(self, camera_id: str) -> str:
        """Start new detection session"""
        with self.lock:
            session_id = self.storage.create_session(camera_id)
            
            # Initialize session info
            self.active_sessions[session_id] = {
                "camera_id": camera_id,
                "start_time": time.time(),
                "last_detection_time": time.time(),
                "person_count": 0
            }
            
            # Initialize person tracker
            self.person_trackers[session_id] = {}
            
            # Send session start event
            self.message_broker.send_session_event(
                session_id=session_id,
                event_type="session_started",
                data={
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            print(f"Session {session_id} started for camera {camera_id}")
            return session_id
    
    def update_session(self, session_id: str, detections: List[Dict[str, Any]]) -> bool:
        """Update session with new detections"""
        with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            # Update last detection time
            self.active_sessions[session_id]["last_detection_time"] = time.time()
            
            # Update person information
            current_persons = set()
            for detection in detections:
                if detection['class_name'] == 'person':
                    # In a real application, there would be person tracking logic here
                    # For now, just use index as ID
                    person_id = detection.get('person_id', len(current_persons))
                    current_persons.add(person_id)
                    
                    # Update last seen time for person
                    self.person_trackers[session_id][person_id] = time.time()
            
            # Update person count
            person_count = len(current_persons)
            self.active_sessions[session_id]["person_count"] = person_count
            
            # Update session in storage
            self.storage.update_session(session_id, person_count)
            
            # Extend session TTL
            # Note: RedisStorage doesn't have extend_session_ttl method in current implementation
            # We'll rely on regular updates to keep session alive
            
            return True
    
    def _check_timeouts(self):
        """Background timeout checking"""
        while True:
            time.sleep(1)  # Check every second
            
            with self.lock:
                current_time = time.time()
                sessions_to_close = []
                
                for session_id, session_info in list(self.active_sessions.items()):
                    # Check session timeout (no detections for 5 seconds)
                    time_since_last_detection = current_time - session_info["last_detection_time"]
                    
                    if time_since_last_detection > settings.session_timeout:
                        sessions_to_close.append(session_id)
                
                # Close expired sessions
                for session_id in sessions_to_close:
                    self._close_session_internal(session_id)
    
    def _close_session_internal(self, session_id: str):
        """Internal method to close session"""
        if session_id in self.active_sessions:
            # Close session in storage
            self.storage.close_session(session_id)
            
            # Send session close event
            session_info = self.active_sessions[session_id]
            self.message_broker.send_session_event(
                session_id=session_id,
                event_type="session_closed",
                data={
                    "camera_id": session_info["camera_id"],
                    "person_count": session_info["person_count"],
                    "duration": time.time() - session_info["start_time"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Remove session from internal storage
            del self.active_sessions[session_id]
            if session_id in self.person_trackers:
                del self.person_trackers[session_id]
            
            print(f"Session {session_id} closed due to timeout")
    
    def close_session(self, session_id: str):
        """Explicitly close session"""
        with self.lock:
            if session_id in self.active_sessions:
                self._close_session_internal(session_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        with self.lock:
            return session_id in self.active_sessions