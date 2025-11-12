from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from person_detection.domain.entities.detection import Session, FrameDetections


class SessionRepository(ABC):
    """Абстрактный репозиторий для работы с сессиями"""
    
    @abstractmethod
    def create_session(self, session: Session) -> str:
        """Создание новой сессии"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Получение сессии по ID"""
        pass

    @abstractmethod
    def update_session(self, session: Session) -> bool:
        """Обновление сессии"""
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> bool:
        """Закрытие сессии"""
        pass

    @abstractmethod
    def store_frame_detections(self, frame_detections: FrameDetections) -> bool:
        """Сохранение кадра с детекциями"""
        pass

    @abstractmethod
    def extend_session_ttl(self, session_id: str) -> bool:
        """Продление времени жизни сессии"""
        pass