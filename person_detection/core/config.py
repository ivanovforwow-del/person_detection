"""
Configuration module for Person Detection Microservice
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "protected_namespaces": ()}
    
    # Application settings
    app_name: str = "Person Detection Microservice"
    app_version: str = "2.0.0"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", 8000))
    
    # Redis configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_ttl: int = int(os.getenv("REDIS_TTL", 1800))  # 30 minutes in seconds
    
    # RabbitMQ configuration
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_username: str = os.getenv("RABBITMQ_USERNAME", "admin")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "password")
    
    # RTSP/HTTP stream configuration
    rtsp_url: str = os.getenv("RTSP_URL", "")
    
    # Model configuration
    model_path: str = os.getenv("MODEL_PATH", "models/yolo_model.xml")
    weights_path: str = os.getenv("WEIGHTS_PATH", "models/yolo_model.bin")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
    nms_threshold: float = float(os.getenv("NMS_THRESHOLD", 0.4))
    
    # Detection configuration
    detection_interval: float = float(os.getenv("DETECTION_INTERVAL", 0.03))  # seconds
    max_fps: int = int(os.getenv("MAX_FPS", 30))
    
    # Session configuration
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", 5))  # seconds
    session_ttl: int = int(os.getenv("SESSION_TTL", 1800))  # 30 minutes in seconds
    
    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_logging: bool = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
    
    # Performance configuration
    max_concurrent_streams: int = int(os.getenv("MAX_CONCURRENT_STREAMS", 10))
    frame_buffer_size: int = int(os.getenv("FRAME_BUFFER_SIZE", 10))
    
    # Tracking configuration
    tracking_enabled: bool = os.getenv("TRACKING_ENABLED", "True").lower() == "true"
    tracking_max_disappeared: int = int(os.getenv("TRACKING_MAX_DISAPPEARED", 30))
    tracking_max_distance: int = int(os.getenv("TRACKING_MAX_DISTANCE", 100))


settings = Settings()