import redis
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import settings


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=False  # Для работы с бинарными данными
        )
        self.session_ttl = settings.session_ttl # 30 минут в секундах
    
    def create_session(self, camera_id: str) -> str:
        """Создание новой сессии детекции для камеры"""
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        
        session_data = {
            "camera_id": camera_id,
            "start_time": datetime.utcnow().isoformat(),
            "person_count": 0,
            "status": "active"
        }
        
        # Сохраняем сессию с TTL
        self.client.setex(
            session_key, 
            self.session_ttl, 
            json.dumps(session_data)
        )
        
        return session_id
    
    def update_session(self, session_id: str, person_count: int) -> bool:
        """Обновление данных сессии"""
        session_key = f"session:{session_id}"
        
        # Получаем текущие данные сессии
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return False
        
        session_data = json.loads(session_data_raw.decode('utf-8'))
        session_data["person_count"] = person_count
        session_data["last_update"] = datetime.utcnow().isoformat()
        
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
    
    def store_frame(self, session_id: str, frame_id: str, frame_data: bytes, detections: List[Dict]) -> bool:
        """Сохранение кадра с детекциями в сессию"""
        frame_key = f"session:{session_id}:frame:{frame_id}"
        
        frame_info = {
            "frame_id": frame_id,
            "timestamp": datetime.utcnow().isoformat(),
            "detections": detections
        }
        
        # Сохраняем информацию о кадре
        self.client.setex(
            frame_key,
            self.session_ttl,  # TTL такой же как у сессии
            json.dumps(frame_info)
        )
        
        # Сохраняем сам кадр
        frame_data_key = f"session:{session_id}:frame_data:{frame_id}"
        self.client.setex(
            frame_data_key,
            self.session_ttl,
            frame_data
        )
        
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Получение данных сессии"""
        session_key = f"session:{session_id}"
        
        session_data_raw = self.client.get(session_key)
        if not session_data_raw:
            return None
        
        return json.loads(session_data_raw.decode('utf-8'))
    
    def extend_session_ttl(self, session_id: str) -> bool:
        """Продление времени жизни сессии"""
        session_key = f"session:{session_id}"
        
        # Просто обновляем TTL, если сессия существует
        return self.client.expire(session_key, self.session_ttl)
    
    def cleanup_expired_sessions(self):
        """Очистка истекших сессий (неактивных более 30 минут)"""
        # В Redis автоматически удаляются ключи по TTL
        # Этот метод может использоваться для дополнительной очистки при необходимости
        pass