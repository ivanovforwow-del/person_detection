from fastapi import HTTPException
from typing import Dict, Any
from person_detection.presentation.schemas.detection_schema import StreamConfig, SessionInfo
from person_detection.application.use_cases.start_detection_use_case import StartDetectionUseCase, StopDetectionUseCase, GetSessionUseCase


class DetectionController:
    """Контроллер для обработки API запросов детекции"""
    
    def __init__(
        self, 
        start_detection_use_case: StartDetectionUseCase,
        stop_detection_use_case: StopDetectionUseCase,
        get_session_use_case: GetSessionUseCase
    ):
        self.start_detection_use_case = start_detection_use_case
        self.stop_detection_use_case = stop_detection_use_case
        self.get_session_use_case = get_session_use_case

    async def start_detection(self, config: StreamConfig) -> Dict[str, Any]:
        """Запуск детекции по RTSP/HTTP потоку"""
        try:
            result = self.start_detection_use_case.execute(config.camera_id, config.rtsp_url)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def stop_detection(self, camera_id: str) -> Dict[str, Any]:
        """Остановка детекции для указанной камеры"""
        try:
            result = self.stop_detection_use_case.execute(camera_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Получение информации о сессии"""
        try:
            result = self.get_session_use_case.execute(session_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))