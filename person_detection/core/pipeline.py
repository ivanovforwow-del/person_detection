"""
Processing Pipeline for Person Detection Microservice
Implements a modular, optimized pipeline for video processing
"""
from typing import List, Dict, Any, Optional, Callable
import time
import threading
from .interfaces import IStreamProcessor, IDetector, IFrameAnnotator
from .tracker import ObjectTracker
from .observer import EventManager, EventType
from .performance import PerformanceMonitor, FrameBuffer, AdaptiveDetector
from .config import settings


class ProcessingPipeline:
    """Modular processing pipeline for video streams"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.event_manager = EventManager()
        self.tracker = ObjectTracker() if settings.tracking_enabled else None
        self.frame_buffer = FrameBuffer(settings.frame_buffer_size)
        
        # Pipeline components
        self.stream_processor: Optional[IStreamProcessor] = None
        self.detector: Optional[IDetector] = None
        self.adaptive_detector: Optional[AdaptiveDetector] = None
        self.frame_annotator: Optional[IFrameAnnotator] = None
        
        # Pipeline stages
        self.preprocessors: List[Callable] = []
        self.postprocessors: List[Callable] = []
        
        # Performance optimization
        self.target_fps = settings.max_fps
        self.frame_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0.033
        self.last_process_time = 0
    
    def set_components(
        self, 
        stream_processor: IStreamProcessor, 
        detector: IDetector, 
        frame_annotator: IFrameAnnotator
    ):
        """Set pipeline components"""
        self.stream_processor = stream_processor
        self.adaptive_detector = AdaptiveDetector(detector, self.performance_monitor)
        self.frame_annotator = frame_annotator
        self.detector = detector  # Keep reference to original detector
    
    def add_preprocessor(self, func: Callable):
        """Add a preprocessing function to the pipeline"""
        self.preprocessors.append(func)
    
    def add_postprocessor(self, func: Callable):
        """Add a postprocessing function to the pipeline"""
        self.postprocessors.append(func)
    
    def process_frame(self, frame) -> Dict[str, Any]:
        """Process a single frame through the pipeline"""
        start_time = time.time()
        
        # Preprocessing
        for preprocessor in self.preprocessors:
            frame = preprocessor(frame)
        
        # Detection
        detection_start = time.time()
        detections = self.adaptive_detector.detect(frame)
        detection_time = time.time() - detection_start
        
        # Tracking (if enabled)
        if self.tracker:
            detections = self.tracker.update(detections)
        
        # Postprocessing
        for postprocessor in self.postprocessors:
            detections = postprocessor(detections)
        
        # Annotate frame
        annotated_frame = self.frame_annotator.annotate_frame(frame, detections)
        
        # Record performance metrics
        frame_time = time.time() - start_time
        self.performance_monitor.record_frame_time(frame_time)
        
        # Calculate and record FPS
        current_time = time.time()
        if self.last_process_time > 0:
            fps = 1.0 / (current_time - self.last_process_time)
            self.performance_monitor.record_fps(fps)
        self.last_process_time = current_time
        
        # Emit detection event
        self.event_manager.emit(
            EventType.PERSON_DETECTED,
            {
                "detections": detections,
                "frame_time": frame_time,
                "detection_time": detection_time,
                "timestamp": current_time
            }
        )
        
        return {
            "frame": annotated_frame,
            "detections": detections,
            "frame_time": frame_time,
            "detection_time": detection_time
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_monitor.get_system_metrics()
    
    def get_event_manager(self) -> EventManager:
        """Get event manager for the pipeline"""
        return self.event_manager