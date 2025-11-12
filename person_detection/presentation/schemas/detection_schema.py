from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class StreamConfig(BaseModel):
    rtsp_url: str
    camera_id: str = "default"


class DetectionResult(BaseModel):
    session_id: str
    person_count: int
    detections: List[Dict]
    frame_id: str
    timestamp: float


class SessionInfo(BaseModel):
    session_id: str
    camera_id: str
    start_time: datetime
    person_count: int
    status: str
    last_update: Optional[datetime] = None
    end_time: Optional[datetime] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: float
    performance_metrics: Dict[str, float]
    active_streams: int