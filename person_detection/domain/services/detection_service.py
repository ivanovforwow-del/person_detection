from abc import ABC, abstractmethod
from typing import List
from person_detection.domain.entities.detection import Detection, FrameDetections


class DetectionService(ABC):
    """Абстрактный сервис для детекции объектов"""
    
    @abstractmethod
    def detect(self, image) -> List[Detection]:
        """Детекция объектов на изображении"""
        pass

    @abstractmethod
    def preprocess_image(self, image) -> any:
        """Предобработка изображения для модели"""
        pass

    @abstractmethod
    def postprocess(self, outputs, original_image_shape) -> List[Detection]:
        """Постобработка результатов детекции"""
        pass