"""
Redis Storage Implementation for Person Detection Microservice
"""
import redis
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import settings
from ..core.interfaces import IDataStorage


class RedisStorage(IDataStorage):
    """Redis-based data storage implementation"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=False  # For binary data handling
        )
        self.session_ttl = settings.session_ttl  # 30 minutes in seconds
    
    def create_session(self, camera_id: str) -> str:
        """Create new detection session for camera"""
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        
        session_data = {
            "camera_id": camera_id,
            "start_time": datetime.utcnow().isoformat(),
            "person_count": 0,
            "status": "active"
        }
        
        # Store session with TTL
        self.client.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        return session_id
    
    def update_session(self, session_id: str, person_count: int) -> bool:
        """Update session data"""
        session_key = f"session:{session_id}"
        
        # Get current session data
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return False
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        session_data["person_count"] = person_count
        session_data["last_update"] = datetime.utcnow().isoformat()
        
        # Update session with TTL
        self.client.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        return True
    
    def close_session(self, session_id: str) -> bool:
        """Close session"""
        session_key = f"session:{session_id}"
        
        # Get current session data
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return False
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        session_data["end_time"] = datetime.utcnow().isoformat()
        session_data["status"] = "closed"
        
        # Update session without TTL (will be removed later)
        self.client.set(
            session_key,
            json.dumps(session_data)
        )
        
        return True
    
    def store_frame(self, session_id: str, frame_id: str, frame_data: bytes, 
                   detections: List[Dict[str, Any]]) -> bool:
        """Store frame with detections in session"""
        frame_key = f"session:{session_id}:frame:{frame_id}"
        
        frame_info = {
            "frame_id": frame_id,
            "timestamp": datetime.utcnow().isoformat(),
            "detections": detections
        }
        
        # Store frame info
        self.client.setex(
            frame_key,
            self.session_ttl,  # TTL same as session
            json.dumps(frame_info)
        )
        
        # Store frame data
        frame_data_key = f"session:{session_id}:frame_data:{frame_id}"
        self.client.setex(
            frame_data_key,
            self.session_ttl,
            frame_data
        )
        
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"session:{session_id}"
        
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return None
        
        return json.loads(session_data_raw.decode('utf-8'))
    
    def extend_session_ttl(self, session_id: str) -> bool:
        """Extend session time-to-live"""
        session_key = f"session:{session_id}"
        
        # Simply update TTL if session exists
        return self.client.expire(session_key, self.session_ttl)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (inactive for more than 30 minutes)"""
        # Redis automatically removes keys by TTL
        # This method can be used for additional cleanup if needed
        pass