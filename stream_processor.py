import cv2
import numpy as np
import time
from typing import List, Tuple, Dict, Optional
from config import settings


class StreamProcessor:
    def __init__(self):
        self.cap = None
        self.current_frame = None
        self.frame_count = 0
        self.last_frame_time = 0
        self.fps = 0
        
    def connect_to_stream(self, stream_url: str):
        """Подключение к RTSP/HTTP потоку"""
        self.cap = cv2.VideoCapture(stream_url)
        
        if not self.cap.isOpened():
            raise Exception(f"Не удалось подключиться к потоку: {stream_url}")
        
        # Установка разрешения FullHD
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Проверка FPS потока
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"FPS потока: {fps}")
        
        return True
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Чтение кадра из потока"""
        if self.cap is None:
            return False, None
            
        success, frame = self.cap.read()
        
        if not success:
            return False, None
            
        self.current_frame = frame
        self.frame_count += 1
        
        # Расчет реального FPS
        current_time = time.time()
        if self.last_frame_time != 0:
            self.fps = 1.0 / (current_time - self.last_frame_time)
        self.last_frame_time = current_time
        
        return True, frame
    
    def get_fps(self) -> float:
        """Получение текущего FPS"""
        return self.fps
    
    def release(self):
        """Освобождение ресурсов"""
        if self.cap:
            self.cap.release()