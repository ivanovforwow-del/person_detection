"""
Stream Processor Implementation for Person Detection Microservice
"""
from typing import List, Tuple, Dict, Optional
import cv2
import numpy as np
import time
from .interfaces import IStreamProcessor
from .config import settings


class StreamProcessor(IStreamProcessor):
    """Video stream processor for RTSP/HTTP streams"""
    
    def __init__(self):
        self.cap = None
        self.current_frame = None
        self.frame_count = 0
        self.last_frame_time = 0
        self.fps = 0
        self.target_fps = settings.max_fps
        self.frame_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0.033  # Default ~30 FPS
        self.last_process_time = 0
    
    def connect_to_stream(self, stream_url: str) -> bool:
        """Connect to RTSP/HTTP stream"""
        self.cap = cv2.VideoCapture(stream_url)
        
        if not self.cap.isOpened():
            raise Exception(f"Failed to connect to stream: {stream_url}")
        
        # Set FullHD resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Check stream FPS
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Stream FPS: {fps}")
        
        return True
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame from stream with FPS control"""
        if self.cap is None:
            return False, None
            
        # Control FPS by skipping frames if necessary
        current_time = time.time()
        if current_time - self.last_process_time < self.frame_interval:
            # Skip frame to maintain target FPS
            success, _ = self.cap.read()
            return False, None
            
        success, frame = self.cap.read()
        
        if not success:
            return False, None
            
        self.current_frame = frame
        self.frame_count += 1
        self.last_process_time = current_time
        
        # Calculate actual FPS
        if self.last_frame_time != 0:
            self.fps = 1.0 / (current_time - self.last_frame_time)
        self.last_frame_time = current_time
        
        return True, frame
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.fps
    
    def release(self):
        """Release resources"""
        if self.cap:
            self.cap.release()