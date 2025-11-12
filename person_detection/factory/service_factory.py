"""
Service Factory for Person Detection Microservice
Implements Factory pattern for creating service instances
"""
from ..core.detector import YOLODetector
from ..core.stream_processor import StreamProcessor
from ..core.frame_annotator import FrameAnnotator
from ..infrastructure.storage import RedisStorage
from ..infrastructure.messaging import RabbitMQBroker
from ..services.session_manager import SessionManager
from ..services.detection_worker import DetectionWorker


class ServiceFactory:
    """Factory for creating service instances"""
    
    @staticmethod
    def create_detector() -> YOLODetector:
        """Create YOLO detector instance"""
        return YOLODetector()
    
    @staticmethod
    def create_stream_processor() -> StreamProcessor:
        """Create stream processor instance"""
        return StreamProcessor()
    
    @staticmethod
    def create_frame_annotator() -> FrameAnnotator:
        """Create frame annotator instance"""
        return FrameAnnotator()
    
    @staticmethod
    def create_storage() -> RedisStorage:
        """Create storage instance"""
        return RedisStorage()
    
    @staticmethod
    def create_message_broker() -> RabbitMQBroker:
        """Create message broker instance"""
        return RabbitMQBroker()
    
    @staticmethod
    def create_session_manager(storage, message_broker) -> SessionManager:
        """Create session manager instance"""
        return SessionManager(storage, message_broker)
    
    @staticmethod
    def create_detection_worker(
        stream_processor, 
        detector, 
        frame_annotator, 
        storage, 
        message_broker, 
        session_manager
    ) -> DetectionWorker:
        """Create detection worker instance"""
        return DetectionWorker(
            stream_processor,
            detector,
            frame_annotator,
            storage,
            message_broker,
            session_manager
        )
    
    @classmethod
    def create_complete_service_suite(cls):
        """Create a complete suite of services with proper dependencies"""
        # Create core services
        storage = cls.create_storage()
        message_broker = cls.create_message_broker()
        session_manager = cls.create_session_manager(storage, message_broker)
        
        # Create processing services
        detector = cls.create_detector()
        stream_processor = cls.create_stream_processor()
        frame_annotator = cls.create_frame_annotator()
        
        # Create worker
        worker = cls.create_detection_worker(
            stream_processor,
            detector,
            frame_annotator,
            storage,
            message_broker,
            session_manager
        )
        
        return {
            'detector': detector,
            'stream_processor': stream_processor,
            'frame_annotator': frame_annotator,
            'storage': storage,
            'message_broker': message_broker,
            'session_manager': session_manager,
            'worker': worker
        }