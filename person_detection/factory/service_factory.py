from person_detection.core.detection_strategy import YOLODetectionStrategy
from person_detection.core.frame_annotator import FrameAnnotator
from person_detection.core.stream_processor import StreamProcessor
from person_detection.infrastructure.repositories.redis_session_repository import RedisSessionRepository
from person_detection.infrastructure.gateways.rabbitmq_gateway import RabbitMQGateway
from person_detection.services.session_manager import SessionManager
from person_detection.services.detection_worker import DetectionWorker
from config import settings


class ServiceFactory:
    """Фабрика для создания сервисов приложения"""
    
    @staticmethod
    def create_detection_service():
        """Создание сервиса детекции"""
        return YOLODetectionStrategy(
            model_path=settings.model_path,
            weights_path=settings.weights_path,
            confidence_threshold=settings.confidence_threshold
        )
    
    @staticmethod
    def create_frame_annotator():
        """Создание сервиса аннотации кадров"""
        return FrameAnnotator()
    
    @staticmethod
    def create_stream_processor():
        """Создание процессора видеопотоков"""
        return StreamProcessor()
    
    @staticmethod
    def create_session_repository():
        """Создание репозитория сессий"""
        return RedisSessionRepository()
    
    @staticmethod
    def create_detection_gateway():
        """Создание шлюза для взаимодействия с внешними системами"""
        return RabbitMQGateway()
    
    @staticmethod
    def create_session_manager(session_repository=None, detection_gateway=None):
        """Создание менеджера сессий"""
        if session_repository is None:
            session_repository = ServiceFactory.create_session_repository()
        if detection_gateway is None:
            detection_gateway = ServiceFactory.create_detection_gateway()
            
        return SessionManager(session_repository, detection_gateway)
    
    @staticmethod
    def create_detection_worker(
        stream_processor=None,
        detection_service=None,
        frame_annotator=None,
        session_manager=None,
        detection_gateway=None
    ):
        """Создание работника для обработки видеопотока"""
        if stream_processor is None:
            stream_processor = ServiceFactory.create_stream_processor()
        if detection_service is None:
            detection_service = ServiceFactory.create_detection_service()
        if frame_annotator is None:
            frame_annotator = ServiceFactory.create_frame_annotator()
        if session_manager is None:
            session_manager = ServiceFactory.create_session_manager()
        if detection_gateway is None:
            detection_gateway = ServiceFactory.create_detection_gateway()
            
        return DetectionWorker(
            stream_processor=stream_processor,
            detection_service=detection_service,
            frame_annotator=frame_annotator,
            session_manager=session_manager,
            detection_gateway=detection_gateway
        )