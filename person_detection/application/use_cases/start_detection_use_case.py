from abc import ABC, abstractmethod
from typing import Dict, Any
from person_detection.domain.entities.detection import Session


class StartDetectionUseCase(ABC):
    """Абстрактный Use Case для запуска детекции"""
    
    @abstractmethod
    def execute(self, camera_id: str, rtsp_url: str) -> Dict[str, Any]:
        """Выполнение запуска детекции"""
        pass


class StopDetectionUseCase(ABC):
    """Абстрактный Use Case для остановки детекции"""
    
    @abstractmethod
    def execute(self, camera_id: str) -> Dict[str, Any]:
        """Выполнение остановки детекции"""
        pass


class GetSessionUseCase(ABC):
    """Абстрактный Use Case для получения информации о сессии"""
    
    @abstractmethod
    def execute(self, session_id: str) -> Dict[str, Any]:
        """Выполнение получения информации о сессии"""
        pass