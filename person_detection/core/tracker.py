"""
Object Tracker Implementation for Person Detection Microservice
Implements a simple object tracking algorithm
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
from .config import settings


class TrackedObject:
    """Represents a tracked object with its properties"""
    
    def __init__(self, object_id: str, bbox: List[int], centroid: Tuple[int, int]):
        self.id = object_id
        self.bbox = bbox
        self.centroid = centroid
        self.disappeared = 0
        self.positions: List[Tuple[int, int]] = [centroid]
        self.max_positions = 10  # Keep last 10 positions
    
    def update(self, bbox: List[int], centroid: Tuple[int, int]):
        """Update tracked object with new position"""
        self.bbox = bbox
        self.centroid = centroid
        self.disappeared = 0
        
        # Add new position
        self.positions.append(centroid)
        if len(self.positions) > self.max_positions:
            self.positions.pop(0)


class ObjectTracker:
    """Simple object tracker using centroid tracking algorithm"""
    
    def __init__(self):
        self.next_object_id = 0
        self.objects: Dict[str, TrackedObject] = {}
        self.disappeared: Dict[str, int] = {}
        self.max_disappeared = settings.tracking_max_disappeared
        self.max_distance = settings.tracking_max_distance
    
    def register(self, bbox: List[int]):
        """Register a new object"""
        object_id = str(self.next_object_id)
        centroid = self._calculate_centroid(bbox)
        
        self.objects[object_id] = TrackedObject(object_id, bbox, centroid)
        self.disappeared[object_id] = 0
        self.next_object_id += 1
        
        return object_id
    
    def deregister(self, object_id: str):
        """Deregister an object"""
        del self.objects[object_id]
        del self.disappeared[object_id]
    
    def _calculate_centroid(self, bbox: List[int]) -> Tuple[int, int]:
        """Calculate centroid of bounding box"""
        x_min, y_min, x_max, y_max = bbox
        cx = (x_min + x_max) // 2
        cy = (y_min + y_max) // 2
        return (cx, cy)
    
    def _calculate_distance(self, centroid1: Tuple[int, int], centroid2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between centroids"""
        return np.sqrt((centroid1[0] - centroid2[0])**2 + (centroid1[1] - centroid2[1])**2)
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """Update tracker with new detections"""
        if len(detections) == 0:
            # Mark all existing objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return []
        
        # Calculate centroids for new detections
        input_centroids = []
        for detection in detections:
            bbox = detection['bbox']
            centroid = self._calculate_centroid(bbox)
            input_centroids.append(centroid)
        
        # If no objects are being tracked, register all detections
        if len(self.objects) == 0:
            for i, detection in enumerate(detections):
                object_id = self.register(detection['bbox'])
                detection['person_id'] = object_id
        else:
            # Match existing objects with new detections
            object_centroids = [obj.centroid for obj in self.objects.values()]
            object_ids = list(self.objects.keys())
            
            # Calculate distance matrix
            D = np.linalg.norm(
                np.array(object_centroids)[:, np.newaxis] - np.array(input_centroids), 
                axis=2
            )
            
            # Find minimum distances
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            used_row_indices = set()
            used_col_indices = set()
            
            # Update existing objects with matched detections
            for (row, col) in zip(rows, cols):
                if row in used_row_indices or col in used_col_indices:
                    continue
                
                if D[row, col] > self.max_distance:
                    continue
                
                object_id = object_ids[row]
                detection = detections[col]
                
                # Update tracked object
                self.objects[object_id].update(detection['bbox'], input_centroids[col])
                detection['person_id'] = object_id
                
                used_row_indices.add(row)
                used_col_indices.add(col)
            
            # Handle unmatched detections (new objects)
            unused_col_indices = set(range(0, len(detections))).difference(used_col_indices)
            for col in unused_col_indices:
                detection = detections[col]
                object_id = self.register(detection['bbox'])
                detection['person_id'] = object_id
            
            # Handle unmatched existing objects (disappeared)
            unused_row_indices = set(range(0, len(self.objects))).difference(used_row_indices)
            for row in unused_row_indices:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
        
        # Return updated detections with tracking IDs
        return detections