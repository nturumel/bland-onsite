# LLM Fallback Routing System

A comprehensive system for LLM service fallbacks, cold start scaling, zero-latency routing, and maximum utilization. This system includes traffic routing, session management, and monitoring for small and large LLM models.

## 🏗️ System Architecture

The system consists of three main services:

1. **Redis Service** - Global session and model state management
2. **FastAPI Server** - REST API for session initiation and chat completions
3. **Capacity Planning Service** - Automated scaling based on log monitoring

### Key Features

- ✅ Handle cold starts smoothly by over-provisioning
- ✅ Minimize latency using automated routing
- ✅ Maximize utilization across available models
- ✅ Session-based routing with Redis caching
- ✅ Automated capacity planning based on log monitoring
- ✅ Comprehensive logging to both console and files

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- UV package manager (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fallback_routing
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start Redis server:**
   ```bash
   # Using Docker (recommended)
   docker run -d -p 6379:6379 redis:alpine
   
   # Or using local Redis
   redis-server
   ```

### Running the Services

#### Option 1: Run All Services Together
```bash
python main.py all
```

#### Option 2: Run Services Individually

1. **Check Redis connection:**
   ```bash
   python main.py redis
   ```

2. **Start API server only:**
   ```bash
   python main.py api
   ```

3. **Start capacity planning service only:**
   ```bash
   python main.py capacity
   ```

## 📡 API Endpoints

Once the API server is running, you can access the following endpoints:

### Health Check
```bash
curl http://localhost:8000/health
```

### Initiate Session
```bash
curl -X POST http://localhost:8000/initiate_call \
  -H "Content-Type: application/json" \
  -d '{"session_id": "optional-session-id"}'
```

### Chat Completion
```bash
curl -X POST http://localhost:8000/chat_completions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "Hello, how are you?",
    "model": "optional-model-override"
  }'
```

## 🔧 Service Details

### 1. Redis Service (`services/redis_service.py`)

- **Purpose**: Global session and model state management
- **Default Configuration**: 
  - Host: localhost
  - Port: 6379
  - Default model: "large-model"
- **Key Features**:
  - Session selector storage with TTL
  - Model state management
  - Health checking

### 2. FastAPI Server (`services/api_server.py`)

- **Purpose**: REST API for session management and chat completions
- **Port**: 8000
- **Endpoints**:
  - `POST /initiate_call` - Start new session
  - `POST /chat_completions` - Process chat requests
  - `GET /health` - Health check
- **Logging**: Console + `.logs/api_server.log`

### 3. Capacity Planning Service (`services/capacity_planning_service.py`)

- **Purpose**: Automated scaling based on log monitoring
- **Configuration**:
  - Check interval: 10 seconds
  - Initial threshold: 1MB
  - Log directory: `.logs`
- **Scaling Logic**:
  - **Scale Up**: When log size exceeds threshold
    - Spins up large model (simulated 3 minutes)
    - Spins up small model (simulated 20 seconds)
    - Doubles threshold after large model spin-up
  - **Scale Down**: When log size < initial threshold AND no small model usage
    - Shuts down small model
    - Resets to large model
    - Resets threshold to original value

## 📊 Monitoring and Logging

### Log Files

All services log to the `.logs/` directory:

- `api_server.log` - FastAPI server logs
- `capacity_planning.log` - Capacity planning service logs

### Log Rotation

- **Size**: 10MB per file
- **Retention**: 7 days
- **Format**: Timestamp | Level | Module:Function:Line - Message

### Console Logging

All services also output colored logs to the console for real-time monitoring.

## 🔄 System Flow

1. **Session Initiation**:
   ```
   Client → API Server → Redis (store session selector) → Response
   ```

2. **Chat Processing**:
   ```
   Client → API Server → Redis (get session selector) → Model Selection → Response
   ```

3. **Capacity Planning**:
   ```
   Log Monitoring → Threshold Check → Model Spin-up → Redis Update
   ```

## 🛠️ Development

### Project Structure
```
fallback_routing/
├── services/
│   ├── __init__.py
│   ├── redis_service.py
│   ├── api_server.py
│   └── capacity_planning_service.py
├── .logs/                    # Log files (created automatically)
├── main.py                   # Main entry point
├── pyproject.toml           # Dependencies
└── README.md
```

### Adding New Services

1. Create a new module in `services/`
2. Import and initialize in `main.py`
3. Add appropriate logging configuration
4. Update this README

### Configuration

Key configuration options can be modified in each service:

- **Redis**: Host, port, database in `RedisService.__init__()`
- **API Server**: Port, host in `start_api_server()`
- **Capacity Planning**: Thresholds, intervals in `CapacityPlanningService.__init__()`

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Failed**:
   - Ensure Redis server is running
   - Check host/port configuration
   - Verify Redis is accessible

2. **Port Already in Use**:
   - Change port in `main.py` or kill existing process
   - Check for other services using port 8000

3. **Permission Errors**:
   - Ensure write permissions for `.logs/` directory
   - Check file permissions

### Debug Mode

For detailed debugging, modify log levels in each service:

```python
logger.add(sys.stdout, level="DEBUG")
```

## 📈 Performance Considerations

- **Redis**: Use connection pooling for high throughput
- **API Server**: Consider async processing for multiple requests
- **Capacity Planning**: Adjust monitoring intervals based on load
- **Logging**: Monitor log file sizes to prevent disk space issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
