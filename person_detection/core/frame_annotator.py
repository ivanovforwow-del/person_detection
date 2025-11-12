import cv2
import numpy as np
from typing import List
import uuid
from person_detection.domain.entities.detection import Detection
from person_detection.domain.services.frame_annotation_service import FrameAnnotationService


class FrameAnnotator(FrameAnnotationService):
    """Сервис для аннотации кадров"""
    
    def __init__(self):
        self.colors = [
            (255, 0, 0),    # Синий
            (0, 255, 0),    # Зеленый
            (0, 0, 255),    # Красный
            (255, 255, 0),  # Голубой
            (255, 0, 255),  # Пурпурный
            (0, 255, 255),  # Желтый
            (128, 0, 128),  # Фиолетовый
            (255, 165, 0),  # Оранжевый
            (0, 128, 128),  # Бирюзовый
            (128, 128, 0),  # Оливковый
        ]

    def annotate_frame(self, frame: np.ndarray, detections: List[Detection], person_mapping: dict = None) -> np.ndarray:
        """Аннотирование кадра с детекциями"""
        annotated_frame = frame.copy()
        
        if person_mapping is None:
            person_mapping = {}
        
        for i, detection in enumerate(detections):
            if detection.class_name == 'person':
                bbox = detection.bbox
                confidence = detection.confidence
                
                # Получаем ID персоны или создаем новый
                person_id = detection.person_id or i
                if person_id not in person_mapping:
                    person_mapping[person_id] = f"Person{len(person_mapping) + 1}"
                
                person_label = person_mapping[person_id]
                
                # Получаем цвет для этой персоны
                color_idx = hash(person_id) % len(self.colors)  # Используем hash для стабильного цвета
                color = self.colors[color_idx]
                
                # Рисуем bounding box
                x_min, y_min, x_max, y_max = bbox
                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), color, 2)
                
                # Рисуем подпись
                label = f"{person_label}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                # Фон для текста
                cv2.rectangle(
                    annotated_frame,
                    (x_min, y_min - label_size[1] - 10),
                    (x_min + label_size[0], y_min),
                    color,
                    -1
                )
                
                # Текст
                cv2.putText(
                    annotated_frame,
                    label,
                    (x_min, y_min - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
        
        return annotated_frame

    def save_annotated_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Сохранение аннотированного кадра"""
        try:
            success = cv2.imwrite(filename, frame)
            return success
        except Exception as e:
            print(f"Ошибка сохранения кадра: {e}")
            return False

    def encode_frame(self, frame: np.ndarray, format: str = '.jpg', quality: int = 85) -> bytes:
        """Кодирование кадра в байты"""
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encoded_image = cv2.imencode(format, frame, encode_param)
            if result:
                return encoded_image.tobytes()
            else:
                raise Exception("Не удалось закодировать изображение")
        except Exception as e:
            print(f"Ошибка кодирования кадра: {e}")
            raise