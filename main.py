from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import threading
import uvicorn
from typing import Dict, List
import cv2
import numpy as np
import uuid
import time

from config import settings
from stream_processor import StreamProcessor
from yolo_detector import YOLODetector
from redis_client import RedisClient
from rabbitmq_client import RabbitMQClient
from frame_annotator import FrameAnnotator
from session_manager import SessionManager
from logger_config import app_logger, stream_logger, detection_logger, get_performance_metrics


app = FastAPI(title="Person Detection Microservice", version="1.0.0")


class StreamConfig(BaseModel):
    rtsp_url: str
    camera_id: str = "default"


class DetectionResult(BaseModel):
    session_id: str
    person_count: int
    detections: List[Dict]
    frame_id: str
    timestamp: float


# Глобальные переменные для сервисов
stream_processor: StreamProcessor = None
yolo_detector: YOLODetector = None
redis_client: RedisClient = None
rabbitmq_client: RabbitMQClient = None
frame_annotator: FrameAnnotator = None
session_manager: SessionManager = None

# Словарь для хранения активных сессий обработки потока
active_streams: Dict[str, threading.Thread] = {}


def initialize_services():
    """Инициализация всех сервисов"""
    global stream_processor, yolo_detector, redis_client, rabbitmq_client, frame_annotator, session_manager
    
    try:
        # Инициализация сервисов
        redis_client = RedisClient()
        rabbitmq_client = RabbitMQClient()
        stream_processor = StreamProcessor()
        yolo_detector = YOLODetector()
        frame_annotator = FrameAnnotator()
        session_manager = SessionManager(redis_client, rabbitmq_client)
        
        app_logger.info("Все сервисы успешно инициализированы")
        
    except Exception as e:
        app_logger.error(f"Ошибка инициализации сервисов: {e}")
        raise


def process_stream(camera_id: str, rtsp_url: str):
    """Функция обработки видео потока в отдельном потоке"""
    stream_logger.info(f"Начало обработки потока для камеры {camera_id}: {rtsp_url}")
    
    try:
        # Подключение к потоку
        stream_processor.connect_to_stream(rtsp_url)
        
        # Инициализация сессии
        session_id = session_manager.start_session(camera_id)
        last_detections = []
        
        # Словарь для отслеживания ID персон в сессии
        person_mapping = {}
        
        while session_manager.is_session_active(session_id):
            # Чтение кадра
            success, frame = stream_processor.read_frame()
            if not success:
                stream_logger.warning(f"Не удалось получить кадр из потока {rtsp_url}")
                time.sleep(0.1)  # Пауза перед повторной попыткой
                continue
            
            # Детекция людей на кадре
            detections = yolo_detector.detect(frame)
            
            # Обновление сессии с новыми детекциями
            session_manager.update_session(session_id, detections)
            
            # Аннотирование кадра
            annotated_frame = frame_annotator.annotate_frame(frame, detections, person_mapping)
            
            # Кодирование кадра для сохранения в Redis
            frame_bytes = frame_annotator.encode_frame(annotated_frame)
            
            # Генерация ID кадра
            frame_id = str(uuid.uuid4())
            
            # Сохранение кадра в Redis
            redis_client.store_frame(session_id, frame_id, frame_bytes, detections)
            
            # Логирование производительности
            if stream_processor.get_fps() > 0:
                detection_logger.info(f"FPS: {stream_processor.get_fps():.2f}, Найдено людей: {len(detections)}")
            
            # Обновление last_detections для возможного использования в других частях системы
            last_detections = detections
            
            # Маленькая задержка для управления FPS
            time.sleep(0.03)  # ~33 FPS максимум, но реальный FPS зависит от производительности детекции
        
    except Exception as e:
        stream_logger.error(f"Ошибка в процессе обработки потока {rtsp_url}: {e}")
    finally:
        # Закрытие сессии при завершении обработки
        if 'session_id' in locals():
            session_manager.close_session(session_id)
        stream_processor.release()
        stream_logger.info(f"Обработка потока для камеры {camera_id} завершена")


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    initialize_services()


@app.post("/start_detection", response_model=dict)
async def start_detection(config: StreamConfig):
    """Запуск детекции по RTSP/HTTP потоку"""
    try:
        # Проверка, что поток еще не обрабатывается
        if config.camera_id in active_streams and active_streams[config.camera_id].is_alive():
            raise HTTPException(status_code=400, detail="Поток для этой камеры уже обрабатывается")
        
        # Создание и запуск потока обработки
        detection_thread = threading.Thread(
            target=process_stream,
            args=(config.camera_id, config.rtsp_url),
            daemon=True
        )
        detection_thread.start()
        
        # Сохраняем поток в списке активных
        active_streams[config.camera_id] = detection_thread
        
        return {
            "status": "success",
            "message": f"Обработка потока для камеры {config.camera_id} запущена",
            "camera_id": config.camera_id
        }
        
    except Exception as e:
        app_logger.error(f"Ошибка запуска детекции: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop_detection", response_model=dict)
async def stop_detection(camera_id: str):
    """Остановка детекции для указанной камеры"""
    try:
        if camera_id not in active_streams:
            raise HTTPException(status_code=404, detail="Поток для этой камеры не найден")
        
        # В текущей реализации мы не можем напрямую остановить поток
        # Вместо этого мы просто удаляем его из списка активных
        # Сессия будет закрыта по таймауту в SessionManager
        del active_streams[camera_id]
        
        return {
            "status": "success",
            "message": f"Обработка потока для камеры {camera_id} остановлена",
            "camera_id": camera_id
        }
        
    except Exception as e:
        app_logger.error(f"Ошибка остановки детекции: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=dict)
async def health_check():
    """Проверка состояния сервиса"""
    metrics = get_performance_metrics()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "performance_metrics": metrics,
        "active_streams": len([k for k, v in active_streams.items() if v.is_alive()])
    }


@app.get("/session/{session_id}", response_model=dict)
async def get_session(session_id: str):
    """Получение информации о сессии"""
    try:
        session_data = redis_client.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        
        return {
            "session_id": session_id,
            "data": session_data
        }
    except Exception as e:
        app_logger.error(f"Ошибка получения информации о сессии: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Модуль может использоваться как в standalone режиме, так и как часть другого приложения
def run_service(host: str = "0.0.0.0", port: int = 8000):
    """Запуск сервиса детекции людей"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)