"""
Performance Optimization Components for Person Detection Microservice
"""
import time
import threading
from typing import Dict, Any, Optional, Callable
from collections import deque
import psutil
import os
from .config import settings


class PerformanceMonitor:
    """Performance monitoring and optimization"""
    
    def __init__(self):
        self.frame_times = deque(maxlen=100)  # Keep last 100 frame times
        self.detection_times = deque(maxlen=100)  # Keep last 100 detection times
        self.fps_history = deque(maxlen=50)  # Keep last 50 FPS values
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_frame_time(self, frame_time: float):
        """Record time taken to process a frame"""
        with self.lock:
            self.frame_times.append(frame_time)
    
    def record_detection_time(self, detection_time: float):
        """Record time taken for detection"""
        with self.lock:
            self.detection_times.append(detection_time)
    
    def record_fps(self, fps: float):
        """Record FPS value"""
        with self.lock:
            self.fps_history.append(fps)
    
    def get_avg_frame_time(self) -> float:
        """Get average frame processing time"""
        with self.lock:
            if not self.frame_times:
                return 0.0
            return sum(self.frame_times) / len(self.frame_times)
    
    def get_avg_detection_time(self) -> float:
        """Get average detection time"""
        with self.lock:
            if not self.detection_times:
                return 0.0
            return sum(self.detection_times) / len(self.detection_times)
    
    def get_current_fps(self) -> float:
        """Get current FPS"""
        with self.lock:
            if not self.fps_history:
                return 0.0
            return sum(self.fps_history) / len(self.fps_history)
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "avg_frame_time": self.get_avg_frame_time(),
            "avg_detection_time": self.get_avg_detection_time(),
            "current_fps": self.get_current_fps(),
            "uptime_seconds": self.get_uptime()
        }


class FrameBuffer:
    """Thread-safe frame buffer for optimized processing"""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.buffer = deque()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    
    def put(self, frame):
        """Add frame to buffer"""
        with self.condition:
            while len(self.buffer) >= self.max_size:
                # Remove oldest frame if buffer is full
                self.buffer.popleft()
            
            self.buffer.append(frame)
            self.condition.notify()
    
    def get(self, timeout: Optional[float] = None):
        """Get frame from buffer"""
        with self.condition:
            while len(self.buffer) == 0:
                if not self.condition.wait(timeout):
                    return None
            
            frame = self.buffer.popleft()
            return frame
    
    def size(self) -> int:
        """Get current buffer size"""
        with self.lock:
            return len(self.buffer)
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        with self.lock:
            return len(self.buffer) == 0
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        with self.lock:
            return len(self.buffer) >= self.max_size


class AdaptiveDetector:
    """Adaptive detection that adjusts based on performance"""
    
    def __init__(self, detector, performance_monitor: PerformanceMonitor):
        self.detector = detector
        self.performance_monitor = performance_monitor
        self.target_fps = settings.max_fps
        self.skip_frames = 0  # Number of frames to skip
        self.frame_count = 0
        self.detection_enabled = True
        self.adaptation_threshold = 0.8  # 80% of target FPS
    
    def detect(self, image):
        """Detect with adaptive frame skipping"""
        self.frame_count += 1
        
        # Check if we should skip this frame based on performance
        current_fps = self.performance_monitor.get_current_fps()
        target_fps = self.target_fps
        
        if current_fps < target_fps * self.adaptation_threshold and self.skip_frames < 5:
            # Performance is below threshold, increase frame skipping
            self.skip_frames += 1
        elif current_fps > target_fps * 0.95 and self.skip_frames > 0:
            # Performance is good, reduce frame skipping
            self.skip_frames -= 1
        
        if self.skip_frames > 0 and self.frame_count % (self.skip_frames + 1) != 0:
            # Skip detection for this frame
            return []
        
        # Perform detection
        start_time = time.time()
        results = self.detector.detect(image)
        detection_time = time.time() - start_time
        
        # Record performance metrics
        self.performance_monitor.record_detection_time(detection_time)
        
        return results


class ThreadPool:
    """Simple thread pool for parallel processing"""
    
    def __init__(self, num_threads: int = 4):
        self.num_threads = num_threads
        self.workers = []
        self.task_queue = deque()
        self.condition = threading.Condition()
        self.shutdown = False
        
        # Start worker threads
        for i in range(self.num_threads):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Worker thread function"""
        while True:
            with self.condition:
                while not self.task_queue and not self.shutdown:
                    self.condition.wait()
                
                if self.shutdown:
                    break
                
                if self.task_queue:
                    task, args, kwargs = self.task_queue.popleft()
            
            if task:
                try:
                    task(*args, **kwargs)
                except Exception as e:
                    print(f"Error in thread pool task: {e}")
    
    def submit(self, func: Callable, *args, **kwargs):
        """Submit a task to the thread pool"""
        with self.condition:
            if not self.shutdown:
                self.task_queue.append((func, args, kwargs))
                self.condition.notify()
    
    def shutdown_pool(self):
        """Shutdown the thread pool"""
        with self.condition:
            self.shutdown = True
            self.condition.notify_all()
        
        for worker in self.workers:
            worker.join()