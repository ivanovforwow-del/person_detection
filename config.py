from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "protected_namespaces": ()}
    
    # Redis configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    
    # RabbitMQ configuration
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", 5672))
    rabbitmq_username: str = os.getenv("RABBITMQ_USERNAME", "admin")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "password")
    
    # RTSP/HTTP stream configuration
    rtsp_url: str = os.getenv("RTSP_URL", "")
    
    # OpenVINO configuration
    model_path: str = os.getenv("MODEL_PATH", "models/yolo_model.xml")
    weights_path: str = os.getenv("WEIGHTS_PATH", "models/yolo_model.bin")
    
    # Detection configuration
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
    nms_threshold: float = float(os.getenv("NMS_THRESHOLD", 0.4))
    
    # Session configuration
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", 5))  # seconds
    session_ttl: int = int(os.getenv("SESSION_TTL", 1800))  # 30 minutes in seconds
    
    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_logging: bool = os.getenv("ENABLE_LOGGING", "False").lower() == "true"


settings = Settings()