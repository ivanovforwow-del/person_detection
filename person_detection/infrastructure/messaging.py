"""
RabbitMQ Messaging Implementation for Person Detection Microservice
"""
import pika
import json
from typing import Dict, Any
from .config import settings
from ..core.interfaces import IMessageBroker
import logging


class RabbitMQBroker(IMessageBroker):
    """RabbitMQ-based message broker implementation"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(settings.rabbitmq_username, settings.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange for detection events
            self.channel.exchange_declare(exchange='detection_events', exchange_type='topic', durable=True)
            
            logging.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logging.error(f"Error connecting to RabbitMQ: {e}")
            raise
    
    def send_session_event(self, session_id: str, event_type: str, data: Dict[str, Any] = None):
        """Send session event to RabbitMQ"""
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
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logging.info(f"Session event {event_type} sent to RabbitMQ: {session_id}")
            
        except Exception as e:
            logging.error(f"Error sending event to RabbitMQ: {e}")
            # Attempt reconnection on error
            self.reconnect()
            # Retry sending
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
                logging.error(f"Error retrying event send to RabbitMQ: {retry_error}")
    
    def reconnect(self):
        """Reconnect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass  # Ignore errors during closing
        
        self.connect()
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logging.info("RabbitMQ connection closed")
        except Exception as e:
            logging.error(f"Error closing RabbitMQ connection: {e}")