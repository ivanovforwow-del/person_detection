"""
Detection Worker Service for Person Detection Microservice
"""
import threading
import time
import uuid
from typing import Dict, List, Any
from .config import settings
from ..core.interfaces import (
    IStreamProcessor, IDetector, IFrameAnnotator, 
    IDataStorage, IMessageBroker, ISessionManager
)


class DetectionWorker:
    """Worker for processing video streams and detecting persons"""
    
    def __init__(
        self,
        stream_processor: IStreamProcessor,
        detector: IDetector,
        frame_annotator: IFrameAnnotator,
        storage: IDataStorage,
        message_broker: IMessageBroker,
        session_manager: ISessionManager
    ):
        self.stream_processor = stream_processor
        self.detector = detector
        self.frame_annotator = frame_annotator
        self.storage = storage
        self.message_broker = message_broker
        self.session_manager = session_manager
        
        self.active = False
        self.thread = None
        self.person_mapping = {}
    
    def start_detection(self, camera_id: str, rtsp_url: str) -> str:
        """Start person detection for a camera stream"""
        # Start new session
        session_id = self.session_manager.start_session(camera_id)
        
        # Start processing thread
        self.active = True
        self.thread = threading.Thread(
            target=self._process_stream,
            args=(camera_id, rtsp_url, session_id),
            daemon=True
        )
        self.thread.start()
        
        return session_id
    
    def stop_detection(self, session_id: str):
        """Stop person detection for a session"""
        self.active = False
        self.session_manager.close_session(session_id)
    
    def _process_stream(self, camera_id: str, rtsp_url: str, session_id: str):
        """Process video stream in a separate thread"""
        print(f"Starting stream processing for camera {camera_id}: {rtsp_url}")
        
        try:
            # Connect to stream
            self.stream_processor.connect_to_stream(rtsp_url)
            
            while self.active and self.session_manager.is_session_active(session_id):
                # Read frame
                success, frame = self.stream_processor.read_frame()
                if not success:
                    time.sleep(0.1)  # Pause before retry
                    continue
                
                # Skip frame if needed for FPS control
                if frame is None:
                    continue
                
                # Detect persons in frame
                detections = self.detector.detect(frame)
                
                # Update session with detections
                self.session_manager.update_session(session_id, detections)
                
                # Annotate frame
                annotated_frame = self.frame_annotator.annotate_frame(
                    frame, detections, self.person_mapping
                )
                
                # Encode frame
                frame_bytes = self.frame_annotator.encode_frame(annotated_frame)
                
                # Generate frame ID
                frame_id = str(uuid.uuid4())
                
                # Store frame in storage
                self.storage.store_frame(session_id, frame_id, frame_bytes, detections)
                
                # Small delay to control processing rate
                time.sleep(settings.detection_interval)
        
        except Exception as e:
            print(f"Error in stream processing {rtsp_url}: {e}")
        finally:
            # Release resources
            self.stream_processor.release()
            print(f"Stream processing for camera {camera_id} completed")