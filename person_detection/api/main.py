"""
Main API for Person Detection Microservice
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Dict, List, Any
import time
from .config import settings
from ..factory.service_factory import ServiceFactory


# Initialize services using factory
services = ServiceFactory.create_complete_service_suite()
worker = services['worker']
session_manager = services['session_manager']
storage = services['storage']


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)


class StreamConfig(BaseModel):
    rtsp_url: str
    camera_id: str = "default"


class DetectionResult(BaseModel):
    session_id: str
    person_count: int
    detections: List[Dict[str, Any]]
    frame_id: str
    timestamp: float


# Dictionary to track active streams
active_streams: Dict[str, str] = {}  # camera_id -> session_id


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Person Detection Microservice started")


@app.post("/start_detection", response_model=dict)
async def start_detection(config: StreamConfig):
    """Start person detection from RTSP/HTTP stream"""
    try:
        # Check if stream is already being processed
        if config.camera_id in active_streams:
            session_id = active_streams[config.camera_id]
            if session_manager.is_session_active(session_id):
                raise HTTPException(
                    status_code=400, 
                    detail="Stream for this camera is already being processed"
                )
            else:
                # Remove inactive session
                del active_streams[config.camera_id]
        
        # Start detection worker
        session_id = worker.start_detection(config.camera_id, config.rtsp_url)
        
        # Track active stream
        active_streams[config.camera_id] = session_id
        
        return {
            "status": "success",
            "message": f"Processing stream for camera {config.camera_id} started",
            "camera_id": config.camera_id,
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"Error starting detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop_detection", response_model=dict)
async def stop_detection(camera_id: str):
    """Stop detection for specified camera"""
    try:
        if camera_id not in active_streams:
            raise HTTPException(status_code=404, detail="Stream for this camera not found")
        
        session_id = active_streams[camera_id]
        
        # Stop the worker
        worker.stop_detection(session_id)
        
        # Remove from active streams
        del active_streams[camera_id]
        
        return {
            "status": "success",
            "message": f"Processing stream for camera {camera_id} stopped",
            "camera_id": camera_id
        }
        
    except Exception as e:
        print(f"Error stopping detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=dict)
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_streams": len(active_streams),
        "version": settings.app_version
    }


@app.get("/session/{session_id}", response_model=dict)
async def get_session(session_id: str):
    """Get session information"""
    try:
        session_data = storage.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "data": session_data
        }
    except Exception as e:
        print(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_service():
    """Run the service"""
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.app_host, 
        port=settings.app_port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_service()