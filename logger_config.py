import logging
import sys
from logging.handlers import RotatingFileHandler
from config import settings
from typing import Dict, Optional
import os


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Настройка логгера"""
    if not settings.enable_logging:
        # Возвращаем логгер с уровнем CRITICAL, чтобы подавить все сообщения
        logger = logging.getLogger(name)
        logger.setLevel(logging.CRITICAL)
        return logger

    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
    )
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Очистка существующих обработчиков
    logger.handlers.clear()
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    if log_file:
        # Создаем директорию для логов, если она не существует
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_log_level() -> int:
    """Получение уровня логирования из настроек"""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(settings.log_level.upper(), logging.INFO)


def initialize_loggers():
    """Инициализация логгеров в зависимости от настроек"""
    level = get_log_level()
    
    # Глобальные логгеры
    global app_logger, stream_logger, detection_logger, redis_logger, rabbitmq_logger
    app_logger = setup_logger("person_detection", "logs/app.log", level)
    stream_logger = setup_logger("stream", "logs/stream.log", level)
    detection_logger = setup_logger("detection", "logs/detection.log", level)
    redis_logger = setup_logger("redis", "logs/redis.log", level)
    rabbitmq_logger = setup_logger("rabbitmq", "logs/rabbitmq.log", level)


def get_performance_metrics() -> Dict[str, float]:
    """Получение метрик производительности"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_percent": process.memory_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "fps": getattr(sys.modules.get('stream_processor', None), 'current_fps', 0) if 'stream_processor' in sys.modules else 0
    }


# Инициализация логгеров
initialize_loggers()