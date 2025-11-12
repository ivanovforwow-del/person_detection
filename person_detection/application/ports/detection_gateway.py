from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from person_detection.domain.entities.detection import Detection, FrameDetections, Session


class DetectionGateway(ABC):
    """Абстрактный порт для взаимодействия с внешними системами"""
    
    @abstractmethod
    def send_session_event(self, session_id: str, event_type: str, data: Dict[str, any] = None):
        """Отправка события сессии во внешнюю систему"""
        pass

    @abstractmethod
    def store_frame(self, session_id: str, frame_id: str, frame_data: bytes, detections: List[Detection]) -> bool:
        """Сохранение кадра с детекциями во внешнюю систему"""
        pass

    @abstractmethod
    def extend_session_ttl(self, session_id: str) -> bool:
        """Продление времени жизни сессии"""
        pass