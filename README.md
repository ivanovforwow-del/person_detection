# Person Detection Microservice

Advanced person detection microservice using computer vision and deep learning technologies. This service processes video streams (RTSP/HTTP) to detect and track people in real-time.

## Features

- Real-time person detection using YOLO model optimized with OpenVINO
- Video stream processing from RTSP/HTTP sources
- Person tracking across frames
- Frame annotation with bounding boxes
- Redis storage for processed frames and detection results
- RabbitMQ messaging for event notifications
- REST API for controlling detection sessions
- Performance monitoring and optimization
- Configurable detection parameters
- Thread-safe concurrent processing

## Architecture

The service follows a microservice architecture with the following components:

### Core Components
- **Detector**: YOLO-based object detection using OpenVINO
- **Stream Processor**: Video stream handling and frame extraction
- **Frame Annotator**: Drawing bounding boxes and labels on frames
- **Tracker**: Object tracking across frames
- **Session Manager**: Managing detection sessions and state

### Infrastructure Components
- **Storage**: Redis-based storage for frames and metadata
- **Messaging**: RabbitMQ for event notifications
- **Configuration**: Pydantic-based settings management

### Service Components
- **Detection Worker**: Threaded video processing
- **Event Manager**: Observer pattern implementation for event handling
- **Performance Monitor**: Metrics collection and optimization

### Design Patterns Implemented
- **Factory Pattern**: ServiceFactory for creating service instances
- **Strategy Pattern**: Different detection algorithms (YOLO, OpenCV HOG)
- **Observer Pattern**: Event management system
- **Interface Segregation**: Clean interfaces for all components
- **Dependency Injection**: Through the ServiceFactory

## Installation

### Prerequisites

- Python 3.8+
- OpenVINO toolkit
- Redis server
- RabbitMQ server
- Docker (optional, for containerized deployment)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd person-detection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up OpenVINO (if not already installed):
```bash
# Follow Intel's OpenVINO installation guide for your platform
source /opt/intel/openvino_2023/setupvars.sh
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

The service uses Pydantic Settings for configuration management. Key settings include:

### Application Settings
- `APP_HOST`: Host address for the API server (default: 0.0.0.0)
- `APP_PORT`: Port for the API server (default: 8000)
- `APP_NAME`: Name of the application (default: "Person Detection Microservice")
- `APP_VERSION`: Version of the application (default: "2.0.0")

### Redis Configuration
- `REDIS_HOST`: Redis server host (default: "localhost")
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_PASSWORD`: Redis password (default: "")
- `REDIS_DB`: Redis database number (default: 0)
- `REDIS_TTL`: Time-to-live for stored data in seconds (default: 1800)

### RabbitMQ Configuration
- `RABBITMQ_HOST`: RabbitMQ server host (default: "localhost")
- `RABBITMQ_PORT`: RabbitMQ server port (default: 5672)
- `RABBITMQ_USERNAME`: RabbitMQ username (default: "admin")
- `RABBITMQ_PASSWORD`: RabbitMQ password (default: "password")

### Model Configuration
- `MODEL_PATH`: Path to the YOLO model XML file (default: "models/yolo_model.xml")
- `WEIGHTS_PATH`: Path to the YOLO model BIN file (default: "models/yolo_model.bin")
- `CONFIDENCE_THRESHOLD`: Minimum confidence for detections (default: 0.5)
- `NMS_THRESHOLD`: Non-maximum suppression threshold (default: 0.4)

### Detection Configuration
- `DETECTION_INTERVAL`: Time between detections in seconds (default: 0.03)
- `MAX_FPS`: Maximum frames per second to process (default: 30)

### Session Configuration
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 5)
- `SESSION_TTL`: Session time-to-live in seconds (default: 1800)

### Performance Configuration
- `MAX_CONCURRENT_STREAMS`: Maximum number of concurrent streams (default: 10)
- `FRAME_BUFFER_SIZE`: Size of frame buffer (default: 10)

### Tracking Configuration
- `TRACKING_ENABLED`: Enable object tracking (default: True)
- `TRACKING_MAX_DISAPPEARED`: Max frames an object can disappear before deregistering (default: 30)
- `TRACKING_MAX_DISTANCE`: Max distance for object matching (default: 100)

## API Endpoints

### Start Detection
```
POST /start_detection
```
Start person detection for a video stream.

Request body:
```json
{
  "rtsp_url": "rtsp://example.com/stream",
  "camera_id": "camera_1"
}
```

Response:
```json
{
  "status": "success",
  "message": "Processing stream for camera camera_1 started",
  "camera_id": "camera_1",
  "session_id": "session_id_here"
}
```

### Stop Detection
```
POST /stop_detection?camera_id={camera_id}
```
Stop person detection for a specific camera.

Response:
```json
{
  "status": "success",
  "message": "Processing stream for camera_1 stopped",
  "camera_id": "camera_1"
}
```

### Health Check
```
GET /health
```
Check service health status.

Response:
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "active_streams": 2,
  "version": "2.0.0"
}
```

### Get Session Info
```
GET /session/{session_id}
```
Get information about a specific session.

Response:
```json
{
  "session_id": "session_id_here",
  "data": {
    "camera_id": "camera_1",
    "start_time": "2023-01-01T00:00:00Z",
    "person_count": 2,
    "status": "active"
  }
}
```

## Performance Optimization

The service includes several performance optimization features:

1. **Adaptive Detection**: Adjusts processing based on system performance
2. **Frame Buffering**: Reduces memory allocation and improves throughput
3. **Thread Pool**: Manages concurrent operations efficiently
4. **Performance Monitoring**: Tracks key metrics for optimization
5. **Configurable Frame Rate**: Limits processing to desired FPS

## Docker Deployment

To run the service using Docker:

1. Build the image:
```bash
docker build -t person-detection .
```

2. Run the container:
```bash
docker run -d \
  --name person-detection \
  -p 8000:8000 \
  -e REDIS_HOST=redis \
  -e RABBITMQ_HOST=rabbitmq \
  person-detection
```

## Development

### Running in Development Mode

```bash
python -m person_detection.api.main
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

The project uses Black for code formatting:
```bash
black .
```

## Event System

The service implements an event system using the Observer pattern:

- `SESSION_STARTED`: Emitted when a session starts
- `SESSION_CLOSED`: Emitted when a session ends
- `PERSON_DETECTED`: Emitted when people are detected
- `FRAME_PROCESSED`: Emitted when a frame is processed
- `ERROR_OCCURRED`: Emitted when an error occurs

## Logging

The service provides comprehensive logging with different log levels and output formats. Logs are written to both console and files (with rotation) based on the configuration.

## Security

- Input validation on all API endpoints
- Configurable authentication (to be implemented)
- Secure connection to Redis and RabbitMQ
- Environment-based configuration to avoid hardcoded secrets

## Scalability

The microservice is designed to be horizontally scalable:
- Stateless design allows multiple instances
- External dependencies (Redis, RabbitMQ) for state management
- Configurable resource limits
- Thread-safe implementation

## Troubleshooting

### Common Issues

1. **Model Loading Errors**: Ensure OpenVINO is properly installed and model files exist
2. **Stream Connection Errors**: Verify RTSP/HTTP URLs are accessible
3. **Performance Issues**: Adjust MAX_FPS and other performance settings
4. **Redis/RabbitMQ Connection Errors**: Check service availability and credentials

### Performance Monitoring

Monitor these key metrics:
- Average frame processing time
- Detection FPS vs. input FPS
- Memory and CPU usage
- Redis and RabbitMQ connection status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.