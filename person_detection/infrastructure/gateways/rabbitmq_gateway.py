import pika
import json
from typing import Dict, Any
from config import settings
import logging
from person_detection.application.ports.detection_gateway import DetectionGateway
from person_detection.domain.entities.detection import Detection


class RabbitMQGateway(DetectionGateway):
    """Реализация порта взаимодействия с RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        """Подключение к RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(settings.rabbitmq_username, settings.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Объявление exchange для событий детекции
            self.channel.exchange_declare(exchange='detection_events', exchange_type='topic', durable=True)
            
            logging.info("Успешно подключено к RabbitMQ")
            
        except Exception as e:
            logging.error(f"Ошибка подключения к RabbitMQ: {e}")
            raise
    
    def send_session_event(self, session_id: str, event_type: str, data: Dict[str, Any] = None):
        """Отправка события сессии в RabbitMQ"""
        try:
            message = {
                "session_id": session_id,
                "event_type": event_type,
                "timestamp": data.get("timestamp") if data else None,
                "camera_id": data.get("camera_id") if data else None,
                "person_count": data.get("person_count") if data else None
            }
            
            if data:
                message.update(data)
            
            routing_key = f"detection.{event_type}"
            
            self.channel.basic_publish(
                exchange='detection_events',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сделать сообщение устойчивым
                )
            )
            
            logging.info(f"Событие сессии {event_type} отправлено в RabbitMQ: {session_id}")
            
        except Exception as e:
            logging.error(f"Ошибка отправки события в RabbitMQ: {e}")
            # Попытка переподключения при ошибке
            self.reconnect()
            # Повторная отправка
            try:
                self.channel.basic_publish(
                    exchange='detection_events',
                    routing_key=f"detection.{event_type}",
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                    )
                )
            except Exception as retry_error:
                logging.error(f"Ошибка повторной отправки события в RabbitMQ: {retry_error}")
    
    def store_frame(self, session_id: str, frame_id: str, frame_data: bytes, detections: list) -> bool:
        """Сохранение кадра с детекциями - в RabbitMQ просто отправляем сообщение о новом кадре"""
        # В этой реализации мы не сохраняем кадр через RabbitMQ, а только отправляем событие
        # Сохранение кадра осуществляется через Redis
        return True

    def extend_session_ttl(self, session_id: str) -> bool:
        """Продление времени жизни сессии - в RabbitMQ не требуется"""
        return True
    
    def reconnect(self):
        """Переподключение к RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass  # Игнорируем ошибки при закрытии
        
        self.connect()
    
    def close(self):
        """Закрытие соединения с RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logging.info("Соединение с RabbitMQ закрыто")
        except Exception as e:
            logging.error(f"Ошибка закрытия соединения с RabbitMQ: {e}")