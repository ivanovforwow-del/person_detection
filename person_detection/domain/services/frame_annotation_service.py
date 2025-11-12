from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np
from person_detection.domain.entities.detection import Detection


class FrameAnnotationService(ABC):
    """Абстрактный сервис для аннотации кадров"""
    
    @abstractmethod
    def annotate_frame(self, frame: np.ndarray, detections: List[Detection], person_mapping: Dict[int, str] = None) -> np.ndarray:
        """Аннотирование кадра с детекциями"""
        pass

    @abstractmethod
    def save_annotated_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Сохранение аннотированного кадра"""
        pass

    @abstractmethod
    def encode_frame(self, frame: np.ndarray, format: str = '.jpg', quality: int = 85) -> bytes:
        """Кодирование кадра в байты"""
        pass