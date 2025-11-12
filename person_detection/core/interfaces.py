"""
Interface definitions for Person Detection Microservice
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2


class IDetector(ABC):
    """Interface for object detection models"""
    
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in an image"""
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for detection"""
        pass
    
    @abstractmethod
    def postprocess(self, outputs: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Postprocess detection outputs"""
        pass


class IStreamProcessor(ABC):
    """Interface for video stream processing"""
    
    @abstractmethod
    def connect_to_stream(self, stream_url: str) -> bool:
        """Connect to video stream"""
        pass
    
    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame from stream"""
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """Get current FPS"""
        pass
    
    @abstractmethod
    def release(self):
        """Release resources"""
        pass


class IFrameAnnotator(ABC):
    """Interface for frame annotation"""
    
    @abstractmethod
    def annotate_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]], 
                      person_mapping: Dict[int, str] = None) -> np.ndarray:
        """Annotate frame with detections"""
        pass
    
    @abstractmethod
    def encode_frame(self, frame: np.ndarray, format: str = '.jpg', quality: int = 85) -> bytes:
        """Encode frame to bytes"""
        pass


class IDataStorage(ABC):
    """Interface for data storage"""
    
    @abstractmethod
    def store_frame(self, session_id: str, frame_id: str, frame_data: bytes, 
                   detections: List[Dict[str, Any]]) -> bool:
        """Store frame with detections"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        pass
    
    @abstractmethod
    def create_session(self, camera_id: str) -> str:
        """Create new session"""
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, person_count: int) -> bool:
        """Update session data"""
        pass
    
    @abstractmethod
    def close_session(self, session_id: str) -> bool:
        """Close session"""
        pass


class IMessageBroker(ABC):
    """Interface for message broker"""
    
    @abstractmethod
    def send_session_event(self, session_id: str, event_type: str, 
                          data: Dict[str, Any] = None) -> None:
        """Send session event"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close connection"""
        pass


class ISessionManager(ABC):
    """Interface for session management"""
    
    @abstractmethod
    def start_session(self, camera_id: str) -> str:
        """Start new detection session"""
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, detections: List[Dict[str, Any]]) -> bool:
        """Update session with new detections"""
        pass
    
    @abstractmethod
    def close_session(self, session_id: str) -> None:
        """Close session"""
        pass
    
    @abstractmethod
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        pass