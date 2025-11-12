from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import asyncio
import threading
import uvicorn
from config import settings
from person_detection.presentation.schemas.detection_schema import StreamConfig
from person_detection.presentation.api.detection_controller import DetectionController
from person_detection.application.use_cases.start_detection_use_case import StartDetectionUseCase, StopDetectionUseCase, GetSessionUseCase
from person_detection.factory.service_factory import ServiceFactory
from logger_config import app_logger, get_performance_metrics
import time


class StartDetectionUseCaseImpl(StartDetectionUseCase):
    """Реализация Use Case для запуска детекции"""
    
    def __init__(self, detection_worker, active_streams):
        self.detection_worker = detection_worker
        self.active_streams = active_streams

    def execute(self, camera_id: str, rtsp_url: str) -> Dict[str, Any]:
        # Проверка, что поток еще не обрабатывается
        if camera_id in self.active_streams and self.active_streams[camera_id].is_alive():
            raise HTTPException(status_code=400, detail="Поток для этой камеры уже обрабатывается")
        
        # Создание и запуск потока обработки
        detection_thread = threading.Thread(
            target=self.detection_worker.process_stream,
            args=(camera_id, rtsp_url),
            daemon=True
        )
        detection_thread.start()
        
        # Сохраняем поток в списке активных
        self.active_streams[camera_id] = detection_thread
        
        return {
            "status": "success",
            "message": f"Обработка потока для камеры {camera_id} запущена",
            "camera_id": camera_id
        }


class StopDetectionUseCaseImpl(StopDetectionUseCase):
    """Реализация Use Case для остановки детекции"""
    
    def __init__(self, active_streams):
        self.active_streams = active_streams

    def execute(self, camera_id: str) -> Dict[str, Any]:
        if camera_id not in self.active_streams:
            raise HTTPException(status_code=404, detail="Поток для этой камеры не найден")
        
        # В текущей реализации мы не можем напрямую остановить поток
        # Вместо этого мы просто удаляем его из списка активных
        # Сессия будет закрыта по таймауту в SessionManager
        del self.active_streams[camera_id]
        
        return {
            "status": "success",
            "message": f"Обработка потока для камеры {camera_id} остановлена",
            "camera_id": camera_id
        }


class GetSessionUseCaseImpl(GetSessionUseCase):
    """Реализация Use Case для получения информации о сессии"""
    
    def __init__(self, session_repository):
        self.session_repository = session_repository

    def execute(self, session_id: str) -> Dict[str, Any]:
        session_data = self.session_repository.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
        
        return {
            "session_id": session_id,
            "data": {
                "camera_id": session_data.camera_id,
                "start_time": session_data.start_time,
                "person_count": session_data.person_count,
                "status": session_data.status,
                "last_update": session_data.last_update,
                "end_time": session_data.end_time
            }
        }


app = FastAPI(title="Person Detection Microservice", version="1.0.0")


# Глобальные переменные для сервисов
detection_worker = None
session_repository = None
controller = None

# Словарь для хранения активных сессий обработки потока
active_streams: Dict[str, threading.Thread] = {}


def initialize_services():
    """Инициализация всех сервисов"""
    global detection_worker, session_repository, controller
    
    try:
        # Инициализация сервисов через фабрику
        detection_worker = ServiceFactory.create_detection_worker()
        session_repository = ServiceFactory.create_session_repository()
        
        # Создание Use Cases
        start_detection_uc = StartDetectionUseCaseImpl(detection_worker, active_streams)
        stop_detection_uc = StopDetectionUseCaseImpl(active_streams)
        get_session_uc = GetSessionUseCaseImpl(session_repository)
        
        # Создание контроллера
        controller = DetectionController(start_detection_uc, stop_detection_uc, get_session_uc)
        
        app_logger.info("Все сервисы успешно инициализированы")
        
    except Exception as e:
        app_logger.error(f"Ошибка инициализации сервисов: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    initialize_services()


@app.post("/start_detection")
async def start_detection(config: StreamConfig):
    """Запуск детекции по RTSP/HTTP потоку"""
    try:
        return await controller.start_detection(config)
    except Exception as e:
        app_logger.error(f"Ошибка запуска детекции: {e}")
        raise


@app.post("/stop_detection")
async def stop_detection(camera_id: str):
    """Остановка детекции для указанной камеры"""
    try:
        return await controller.stop_detection(camera_id)
    except Exception as e:
        app_logger.error(f"Ошибка остановки детекции: {e}")
        raise


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    metrics = get_performance_metrics()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "performance_metrics": metrics,
        "active_streams": len([k for k, v in active_streams.items() if v.is_alive()])
    }


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Получение информации о сессии"""
    try:
        return await controller.get_session(session_id)
    except Exception as e:
        app_logger.error(f"Ошибка получения информации о сессии: {e}")
        raise


# Модуль может использоваться как в standalone режиме, так и как часть другого приложения
def run_service(host: str = "0.0.0.0", port: int = 8000):
    """Запуск сервиса детекции людей"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=800)