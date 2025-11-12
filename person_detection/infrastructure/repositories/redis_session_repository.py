import redis
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from config import settings
from person_detection.domain.entities.detection import Session, FrameDetections
from person_detection.domain.repositories.session_repository import SessionRepository


class RedisSessionRepository(SessionRepository):
    """Реализация репозитория сессий с использованием Redis"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=False  # Для работы с бинарными данными
        )
        self.session_ttl = settings.session_ttl  # 30 минут в секундах

    def create_session(self, session: Session) -> str:
        """Создание новой сессии детекции для камеры"""
        session_key = f"session:{session.session_id}"
        
        session_data = {
            "camera_id": session.camera_id,
            "start_time": session.start_time.isoformat(),
            "person_count": session.person_count,
            "status": session.status
        }
        
        # Сохраняем сессию с TTL
        self.client.setex(
            session_key, 
            self.session_ttl, 
            json.dumps(session_data)
        )
        
        return session.session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Получение данных сессии"""
        session_key = f"session:{session_id}"
        
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return None
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        
        return Session(
            session_id=session_id,
            camera_id=session_data["camera_id"],
            start_time=datetime.fromisoformat(session_data["start_time"]),
            person_count=session_data.get("person_count", 0),
            status=session_data.get("status", "active"),
            last_update=datetime.fromisoformat(session_data["last_update"]) if session_data.get("last_update") else None,
            end_time=datetime.fromisoformat(session_data["end_time"]) if session_data.get("end_time") else None
        )

    def update_session(self, session: Session) -> bool:
        """Обновление данных сессии"""
        session_key = f"session:{session.session_id}"
        
        # Получаем текущие данные сессии
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return False
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        session_data["person_count"] = session.person_count
        session_data["last_update"] = session.last_update.isoformat() if session.last_update else datetime.utcnow().isoformat()
        
        # Обновляем сессию с TTL
        self.client.setex(
            session_key, 
            self.session_ttl, 
            json.dumps(session_data)
        )
        
        return True

    def close_session(self, session_id: str) -> bool:
        """Закрытие сессии"""
        session_key = f"session:{session_id}"
        
        # Получаем текущие данные сессии
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return False
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        session_data["end_time"] = datetime.utcnow().isoformat()
        session_data["status"] = "closed"
        
        # Обновляем сессию без TTL (будет удалена позже)
        self.client.set(
            session_key, 
            json.dumps(session_data)
        )
        
        return True

    def store_frame_detections(self, frame_detections: FrameDetections) -> bool:
        """Сохранение кадра с детекциями в сессию"""
        frame_key = f"session:{frame_detections.session_id}:frame:{frame_detections.frame_id}"
        
        frame_info = {
            "frame_id": frame_detections.frame_id,
            "timestamp": frame_detections.timestamp.isoformat(),
            "detections": [
                {
                    "bbox": detection.bbox,
                    "confidence": detection.confidence,
                    "class_id": detection.class_id,
                    "class_name": detection.class_name,
                    "person_id": detection.person_id
                } for detection in frame_detections.detections
            ]
        }
        
        # Сохраняем информацию о кадре
        self.client.setex(
            frame_key,
            self.session_ttl,  # TTL такой же как у сессии
            json.dumps(frame_info)
        )
        
        # Сохраняем сам кадр если он предоставлен
        if frame_detections.frame_data:
            frame_data_key = f"session:{frame_detections.session_id}:frame_data:{frame_detections.frame_id}"
            self.client.setex(
                frame_data_key,
                self.session_ttl,
                frame_detections.frame_data
            )
        
        return True

    def extend_session_ttl(self, session_id: str) -> bool:
        """Продление времени жизни сессии"""
        session_key = f"session:{session_id}"
        
        # Просто обновляем TTL, если сессия существует
        return self.client.expire(session_key, self.session_ttl)