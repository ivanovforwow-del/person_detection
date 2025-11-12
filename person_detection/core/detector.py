"""
YOLO Detector Implementation for Person Detection Microservice
"""
from typing import List, Dict, Any, Tuple
import numpy as np
import cv2
from openvino.runtime import Core
import time
from .interfaces import IDetector
from .config import settings


class YOLODetector(IDetector):
    """YOLO-based object detector using OpenVINO"""
    
    def __init__(self):
        self.core = Core()
        self.model = None
        self.compiled_model = None
        self.input_layer = None
        self.output_layer = None
        self.input_shape = None
        self.output_shape = None
        self.load_model()
    
    def load_model(self) -> None:
        """Load YOLO model via OpenVINO"""
        try:
            # Read model
            self.model = self.core.read_model(
                model=settings.model_path,
                weights=settings.weights_path
            )
            
            # Compile model for CPU
            self.compiled_model = self.core.compile_model(
                model=self.model,
                device_name="CPU"
            )
            
            # Get input and output layers
            input_layer = self.compiled_model.input(0)
            output_layer = self.compiled_model.output(0)
            
            self.input_layer = input_layer
            self.output_layer = output_layer
            self.input_shape = input_layer.shape
            self.output_shape = output_layer.shape
            
            print(f"Model loaded. Input: {self.input_shape}, Output: {self.output_shape}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for YOLO model"""
        # Get input dimensions
        input_height, input_width = self.input_shape[2], self.input_shape[3]
        
        # Scale image while preserving aspect ratio
        h, w = image.shape[:2]
        scale = min(input_width / w, input_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize image
        image_resized = cv2.resize(image, (new_w, new_h))
        
        # Create black image of required size
        image_input = np.zeros((input_height, input_width, 3), dtype=np.uint8)
        # Place resized image in center
        start_x = (input_width - new_w) // 2
        start_y = (input_height - new_h) // 2
        image_input[start_y:start_y+new_h, start_x:start_x+new_w] = image_resized
        
        # Convert to NCHW format (batch, channels, height, width)
        image_input = image_input.transpose(2, 0, 1) # HWC to CHW
        image_input = image_input.reshape(1, *image_input.shape)  # Add batch dimension
        
        return image_input.astype(np.float32)
    
    def postprocess(self, outputs: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Postprocess detection results"""
        detections = []
        
        # Process YOLO model output
        # Output usually has format [batch, num_detections, 85] for YOLOv5/v8
        # Where 85 = 4 (bbox) + 1 (confidence) + 80 (classes for COCO)
        
        # For person detection we only need class 0 (person)
        height, width = original_shape[:2]
        
        # Filter by confidence threshold
        for detection in outputs[0]:
            # Check model output format
            if len(detection) >= 6:  # [x, y, width, height, confidence, class_id]
                x_center, y_center, w, h = detection[0], detection[1], detection[2], detection[3]
                confidence = detection[4]
                class_id = int(detection[5])
                
                # Filter only persons (class_id = 0 for COCO)
                if class_id == 0 and confidence > settings.confidence_threshold:
                    # Convert normalized coordinates to absolute
                    x_min = int((x_center - w / 2) * width)
                    y_min = int((y_center - h / 2) * height)
                    x_max = int((x_center + w / 2) * width)
                    y_max = int((y_center + h / 2) * height)
                    
                    # Clamp bounding box coordinates to image dimensions
                    x_min = max(0, x_min)
                    y_min = max(0, y_min)
                    x_max = min(width, x_max)
                    y_max = min(height, y_max)
                    
                    detections.append({
                        'bbox': [x_min, y_min, x_max, y_max],
                        'confidence': float(confidence),
                        'class_id': class_id,
                        'class_name': 'person'
                    })
        
        return detections
    
    def detect(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in image"""
        # Preprocess image
        input_tensor = self.preprocess(image)
        
        # Perform inference
        start_time = time.time()
        results = self.compiled_model([input_tensor])
        inference_time = time.time() - start_time
        
        # Get output data
        output = results[self.output_layer]
        
        # Postprocess results
        detections = self.postprocess(output, image.shape)
        
        print(f"Inference completed in {inference_time:.4f}s, found {len(detections)} persons")
        
        return detections