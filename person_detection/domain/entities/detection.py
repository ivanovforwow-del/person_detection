from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Detection:
    """Сущность детекции объекта"""
    bbox: List[int]  # [x_min, y_min, x_max, y_max]
    confidence: float
    class_id: int
    class_name: str
    person_id: Optional[str] = None


@dataclass
class FrameDetections:
    """Сущность кадра с детекциями"""
    frame_id: str
    session_id: str
    timestamp: datetime
    detections: List[Detection]
    frame_data: Optional[bytes] = None


@dataclass
class Session:
    """Сущность сессии детекции"""
    session_id: str
    camera_id: str
    start_time: datetime
    person_count: int = 0
    status: str = "active"
    last_update: Optional[datetime] = None
    end_time: Optional[datetime] = None