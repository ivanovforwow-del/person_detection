from abc import ABC, abstractmethod
import cv2
import numpy as np
from typing import List
from person_detection.domain.entities.detection import Detection
from person_detection.domain.services.detection_service import DetectionService


class DetectionStrategy(ABC):
    """Абстрактная стратегия детекции"""
    
    @abstractmethod
    def detect(self, image) -> List[Detection]:
        """Детекция объектов на изображении"""
        pass


class YOLODetectionStrategy(DetectionStrategy, DetectionService):
    """Стратегия детекции с использованием YOLO и OpenVINO"""
    
    def __init__(self, model_path: str, weights_path: str, confidence_threshold: float = 0.5):
        self.model_path = model_path
        self.weights_path = weights_path
        self.confidence_threshold = confidence_threshold
        self.core = None
        self.model = None
        self.compiled_model = None
        self.input_layer = None
        self.output_layer = None
        self.input_shape = None
        self.output_shape = None
        
        # Загрузка модели
        self.load_model()
    
    def load_model(self):
        """Загрузка YOLO модели через OpenVINO"""
        from openvino.runtime import Core
        
        self.core = Core()
        try:
            # Читаем модель
            self.model = self.core.read_model(
                model=self.model_path, 
                weights=self.weights_path
            )
            
            # Компилируем модель для CPU (оптимизировано под AVX/AVX2)
            self.compiled_model = self.core.compile_model(
                model=self.model, 
                device_name="CPU"
            )
            
            # Получаем входной и выходной слои
            input_layer = self.compiled_model.input(0)
            output_layer = self.compiled_model.output(0)
            
            self.input_layer = input_layer
            self.output_layer = output_layer
            self.input_shape = input_layer.shape
            self.output_shape = output_layer.shape
            
            print(f"Модель загружена. Вход: {self.input_shape}, Выход: {self.output_shape}")
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Предобработка изображения для модели YOLO"""
        # Изменяем размер изображения до нужного размера (обычно 640x640 для YOLO)
        # Но для FullHD модели может потребоваться другой размер
        input_height, input_width = self.input_shape[2], self.input_shape[3]
        
        # Масштабируем изображение с сохранением соотношения сторон
        h, w = image.shape[:2]
        scale = min(input_width / w, input_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Изменяем размер
        image_resized = cv2.resize(image, (new_w, new_h))
        
        # Создаем черное изображение нужного размера
        image_input = np.zeros((input_height, input_width, 3), dtype=np.uint8)
        # Вставляем измененное изображение в центр
        start_x = (input_width - new_w) // 2
        start_y = (input_height - new_h) // 2
        image_input[start_y:start_y+new_h, start_x:start_x+new_w] = image_resized
        
        # Преобразуем в формат NCHW (batch, channels, height, width)
        image_input = image_input.transpose(2, 0, 1) # HWC to CHW
        image_input = image_input.reshape(1, *image_input.shape)  # Add batch dimension
        
        return image_input.astype(np.float32)
    
    def postprocess(self, outputs, original_image_shape) -> List[Detection]:
        """Постобработка результатов детекции"""
        from person_detection.domain.entities.detection import Detection
        
        detections = []
        
        # Обработка вывода модели YOLO
        # Вывод модели обычно имеет формат [batch, num_detections, 85] для YOLOv5/v8
        # Где 85 = 4 (bbox) + 1 (confidence) + 80 (classes для COCO)
        
        # Для детекции людей нам нужен только класс 0 (person)
        height, width = original_image_shape[:2]
        
        # Фильтрация по порогу уверенности
        for detection in outputs[0]:
            # Проверяем формат вывода модели
            if len(detection) >= 6:  # [x, y, width, height, confidence, class_id]
                x_center, y_center, w, h = detection[0], detection[1], detection[2], detection[3]
                confidence = detection[4]
                class_id = int(detection[5])
                
                # Фильтруем только людей (class_id = 0 для COCO)
                if class_id == 0 and confidence > self.confidence_threshold:
                    # Преобразуем нормализованные координаты в абсолютные
                    x_min = int((x_center - w / 2) * width)
                    y_min = int((y_center - h / 2) * height)
                    x_max = int((x_center + w / 2) * width)
                    y_max = int((y_center + h / 2) * height)
                    
                    # Ограничиваем координаты рамки размерами изображения
                    x_min = max(0, x_min)
                    y_min = max(0, y_min)
                    x_max = min(width, x_max)
                    y_max = min(height, y_max)
                    
                    detections.append(Detection(
                        bbox=[x_min, y_min, x_max, y_max],
                        confidence=float(confidence),
                        class_id=class_id,
                        class_name='person'
                    ))
        
        return detections
    
    def detect(self, image) -> List[Detection]:
        """Детекция объектов на изображении"""
        import time
        
        # Предобработка изображения
        input_tensor = self.preprocess_image(image)
        
        # Выполнение инференса
        start_time = time.time()
        results = self.compiled_model([input_tensor])
        inference_time = time.time() - start_time
        
        # Получение выходных данных
        output = results[self.output_layer]
        
        # Постобработка результатов
        detections = self.postprocess(output, image.shape)
        
        print(f"Инференс выполнен за {inference_time:.4f} сек, найдено {len(detections)} человек")
        
        return detections