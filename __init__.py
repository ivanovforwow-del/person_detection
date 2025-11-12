"""
Пакет для детекции людей в RTSP/HTTP потоках
"""

from .main import app, run_service
from .config import settings
from .yolo_detector import YOLODetector
from .stream_processor import StreamProcessor
from .redis_client import RedisClient
from .rabbitmq_client import RabbitMQClient
from .frame_annotator import FrameAnnotator
from .session_manager import SessionManager

__version__ = "1.0.0"
__author__ = "Your Name"

__all__ = [
    "app",
    "run_service",
    "settings",
    "YOLODetector",
    "StreamProcessor",
    "RedisClient",
    "RabbitMQClient",
    "FrameAnnotator",
    "SessionManager",
]