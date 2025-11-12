"""
Frame Annotator Implementation for Person Detection Microservice
"""
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
import uuid
from .interfaces import IFrameAnnotator


class FrameAnnotator(IFrameAnnotator):
    """Frame annotation with detections"""
    
    def __init__(self):
        self.colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
            (128, 0, 128),  # Purple
            (255, 165, 0),  # Orange
            (0, 128, 128),  # Teal
            (128, 128, 0),  # Olive
        ]
    
    def annotate_frame(self, frame: np.ndarray, detections: List[Dict[str, Any]], 
                      person_mapping: Dict[int, str] = None) -> np.ndarray:
        """Annotate frame with detections"""
        annotated_frame = frame.copy()
        
        if person_mapping is None:
            person_mapping = {}
        
        for i, detection in enumerate(detections):
            if detection['class_name'] == 'person':
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # Get person ID or create new one
                person_id = detection.get('person_id', i)
                if person_id not in person_mapping:
                    person_mapping[person_id] = f"Person{len(person_mapping) + 1}"
                
                person_label = person_mapping[person_id]
                
                # Get color for this person
                color_idx = person_id % len(self.colors)
                color = self.colors[color_idx]
                
                # Draw bounding box
                x_min, y_min, x_max, y_max = bbox
                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), color, 2)
                
                # Draw label
                label = f"{person_label}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                # Text background
                cv2.rectangle(
                    annotated_frame,
                    (x_min, y_min - label_size[1] - 10),
                    (x_min + label_size[0], y_min),
                    color,
                    -1
                )
                
                # Text
                cv2.putText(
                    annotated_frame,
                    label,
                    (x_min, y_min - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
        
        return annotated_frame
    
    def encode_frame(self, frame: np.ndarray, format: str = '.jpg', quality: int = 85) -> bytes:
        """Encode frame to bytes"""
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encoded_image = cv2.imencode(format, frame, encode_param)
            if result:
                return encoded_image.tobytes()
            else:
                raise Exception("Failed to encode image")
        except Exception as e:
            print(f"Error encoding frame: {e}")
            raise