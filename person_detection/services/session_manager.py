import time
import threading
from typing import Dict, List
from datetime import datetime
from config import settings
from person_detection.domain.entities.detection import Detection
from person_detection.domain.repositories.session_repository import SessionRepository
from person_detection.application.ports.detection_gateway import DetectionGateway


class SessionManager:
    """Менеджер сессий детекции"""
    
    def __init__(self, session_repository: SessionRepository, detection_gateway: DetectionGateway):
        self.session_repository = session_repository
        self.detection_gateway = detection_gateway
        self.active_sessions: Dict[str, Dict] = {}  # session_id -> session_info
        self.person_trackers: Dict[str, Dict] = {}  # session_id -> {person_id -> last_seen_time}
        self.lock = threading.Lock()
        
        # Запуск фонового потока для проверки таймаутов
        self.timeout_checker_thread = threading.Thread(target=self._check_timeouts, daemon=True)
        self.timeout_checker_thread.start()
    
    def start_session(self, camera_id: str) -> str:
        """Начало новой сессии детекции"""
        from person_detection.domain.entities.detection import Session
        import uuid
        
        with self.lock:
            session_id = str(uuid.uuid4())
            
            # Создаем сущность сессии
            session = Session(
                session_id=session_id,
                camera_id=camera_id,
                start_time=datetime.utcnow(),
                person_count=0,
                status="active"
            )
            
            # Сохраняем сессию в репозиторий
            self.session_repository.create_session(session)
            
            # Инициализируем информацию о сессии
            self.active_sessions[session_id] = {
                "camera_id": camera_id,
                "start_time": time.time(),
                "last_detection_time": time.time(),
                "person_count": 0
            }
            
            # Инициализируем трекер персон
            self.person_trackers[session_id] = {}
            
            # Отправляем событие начала сессии
            self.detection_gateway.send_session_event(
                session_id=session_id,
                event_type="session_started",
                data={
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            print(f"Сессия {session_id} начата для камеры {camera_id}")
            return session_id
    
    def update_session(self, session_id: str, detections: List[Detection]) -> bool:
        """Обновление сессии с новыми детекциями"""
        with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            # Обновляем время последней детекции
            self.active_sessions[session_id]["last_detection_time"] = time.time()
            
            # Обновляем информацию о персонах
            current_persons = set()
            for detection in detections:
                if detection.class_name == 'person':
                    # В реальном приложении здесь должна быть логика трекинга персон
                    # Пока просто используем индекс как ID
                    person_id = detection.person_id or len(current_persons)
                    current_persons.add(person_id)
                    
                    # Обновляем время последнего обнаружения персоны
                    self.person_trackers[session_id][person_id] = time.time()
            
            # Обновляем количество персон
            person_count = len(current_persons)
            self.active_sessions[session_id]["person_count"] = person_count
            
            # Получаем текущую сессию из репозитория и обновляем
            session = self.session_repository.get_session(session_id)
            if session:
                session.person_count = person_count
                session.last_update = datetime.utcnow()
                self.session_repository.update_session(session)
            
            # Продляем TTL сессии
            self.session_repository.extend_session_ttl(session_id)
            
            return True
    
    def _check_timeouts(self):
        """Фоновая проверка таймаутов сессий и персон"""
        while True:
            time.sleep(1)  # Проверяем каждую секунду
            
            with self.lock:
                current_time = time.time()
                sessions_to_close = []
                
                for session_id, session_info in list(self.active_sessions.items()):
                    # Проверяем таймаут сессии (нет детекций в течение 5 секунд)
                    time_since_last_detection = current_time - session_info["last_detection_time"]
                    
                    if time_since_last_detection > settings.session_timeout:
                        sessions_to_close.append(session_id)
                
                # Закрываем просроченные сессии
                for session_id in sessions_to_close:
                    self._close_session_internal(session_id)
    
    def _close_session_internal(self, session_id: str):
        """Внутренний метод закрытия сессии"""
        if session_id in self.active_sessions:
            # Закрываем сессию в репозитории
            self.session_repository.close_session(session_id)
            
            # Отправляем событие закрытия сессии
            session_info = self.active_sessions[session_id]
            self.detection_gateway.send_session_event(
                session_id=session_id,
                event_type="session_closed",
                data={
                    "camera_id": session_info["camera_id"],
                    "person_count": session_info["person_count"],
                    "duration": time.time() - session_info["start_time"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Удаляем сессию из внутреннего хранилища
            del self.active_sessions[session_id]
            if session_id in self.person_trackers:
                del self.person_trackers[session_id]
            
            print(f"Сессия {session_id} закрыта по таймауту")
    
    def close_session(self, session_id: str):
        """Явное закрытие сессии"""
        with self.lock:
            if session_id in self.active_sessions:
                self._close_session_internal(session_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Проверка активности сессии"""
        with self.lock:
            return session_id in self.active_sessions