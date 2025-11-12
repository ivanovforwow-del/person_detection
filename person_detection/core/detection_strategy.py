"""
Detection Strategy Pattern Implementation for Person Detection Microservice
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import numpy as np
from .interfaces import IDetector


class DetectionStrategy(ABC):
    """Abstract base class for detection strategies"""
    
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in an image"""
        pass


class YOLOStrategy(DetectionStrategy):
    """YOLO-based detection strategy"""
    
    def __init__(self, detector: IDetector):
        self.detector = detector
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect using YOLO model"""
        return self.detector.detect(image)


class OpenCVStrategy(DetectionStrategy):
    """OpenCV-based detection strategy (for comparison)"""
    
    def __init__(self):
        # Initialize OpenCV HOG descriptor for people detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect using OpenCV HOG descriptor"""
        # Resize image to appropriate size for HOG
        resized = cv2.resize(image, (640, 480))
        
        # Detect people
        boxes, weights = self.hog.detectMultiScale(resized, winStride=(8, 8))
        
        detections = []
        for (x, y, w, h), weight in zip(boxes, weights):
            # Scale back to original image size
            scale_x = image.shape[1] / resized.shape[1]
            scale_y = image.shape[0] / resized.shape[0]
            
            x_orig = int(x * scale_x)
            y_orig = int(y * scale_y)
            w_orig = int(w * scale_x)
            h_orig = int(h * scale_y)
            
            detections.append({
                'bbox': [x_orig, y_orig, x_orig + w_orig, y_orig + h_orig],
                'confidence': float(weight),
                'class_id': 0,
                'class_name': 'person'
            })
        
        return detections


class DetectionContext:
    """Context for strategy pattern"""
    
    def __init__(self, strategy: DetectionStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: DetectionStrategy):
        """Set the detection strategy"""
        self._strategy = strategy
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Execute detection using current strategy"""
        return self._strategy.detect(image)