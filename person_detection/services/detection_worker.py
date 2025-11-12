import threading
import time
import uuid
from typing import Dict
from person_detection.core.stream_processor import StreamProcessor
from person_detection.domain.services.detection_service import DetectionService
from person_detection.domain.services.frame_annotation_service import FrameAnnotationService
from person_detection.services.session_manager import SessionManager
from person_detection.application.ports.detection_gateway import DetectionGateway
from logger_config import stream_logger, detection_logger


class DetectionWorker:
    """Работник для обработки видеопотока и детекции объектов"""
    
    def __init__(
        self,
        stream_processor: StreamProcessor,
        detection_service: DetectionService,
        frame_annotator: FrameAnnotationService,
        session_manager: SessionManager,
        detection_gateway: DetectionGateway
    ):
        self.stream_processor = stream_processor
        self.detection_service = detection_service
        self.frame_annotator = frame_annotator
        self.session_manager = session_manager
        self.detection_gateway = detection_gateway
        
    def process_stream(self, camera_id: str, rtsp_url: str):
        """Функция обработки видео потока в отдельном потоке"""
        stream_logger.info(f"Начало обработки потока для камеры {camera_id}: {rtsp_url}")
        
        try:
            # Подключение к потоку
            self.stream_processor.connect_to_stream(rtsp_url)
            
            # Инициализация сессии
            session_id = self.session_manager.start_session(camera_id)
            last_detections = []
            
            # Словарь для отслеживания ID персон в сессии
            person_mapping = {}
            
            while self.session_manager.is_session_active(session_id):
                # Чтение кадра
                success, frame = self.stream_processor.read_frame()
                if not success:
                    stream_logger.warning(f"Не удалось получить кадр из потока {rtsp_url}")
                    time.sleep(0.1)  # Пауза перед повторной попыткой
                    continue
                
                # Детекция людей на кадре
                detections = self.detection_service.detect(frame)
                
                # Обновление сессии с новыми детекциями
                self.session_manager.update_session(session_id, detections)
                
                # Аннотирование кадра
                annotated_frame = self.frame_annotator.annotate_frame(frame, detections, person_mapping)
                
                # Кодирование кадра для сохранения
                frame_bytes = self.frame_annotator.encode_frame(annotated_frame)
                
                # Генерация ID кадра
                frame_id = str(uuid.uuid4())
                
                # Сохранение кадра через gateway
                self.detection_gateway.store_frame(session_id, frame_id, frame_bytes, detections)
                
                # Логирование производительности
                if self.stream_processor.get_fps() > 0:
                    detection_logger.info(f"FPS: {self.stream_processor.get_fps():.2f}, Найдено людей: {len(detections)}")
                
                # Обновление last_detections для возможного использования в других частях системы
                last_detections = detections
                
                # Маленькая задержка для управления FPS
                time.sleep(0.03)  # ~33 FPS максимум, но реальный FPS зависит от производительности детекции
            
        except Exception as e:
            stream_logger.error(f"Ошибка в процессе обработки потока {rtsp_url}: {e}")
        finally:
            # Закрытие сессии при завершении обработки
            if 'session_id' in locals():
                self.session_manager.close_session(session_id)
            self.stream_processor.release()
            stream_logger.info(f"Обработка потока для камеры {camera_id} завершена")