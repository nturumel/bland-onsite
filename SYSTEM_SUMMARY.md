# LLM Fallback Routing System - Complete Implementation

## 🎯 Overview

This system implements the design document requirements with three separate, modular services that work together to provide LLM fallback routing, scaling, and utilization management.

## 🏗️ Architecture Summary

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Service │    │  FastAPI Server │    │Capacity Planning│
│                 │    │                 │    │     Service     │
│ • Model State   │◄──►│ • Session Mgmt  │◄──►│ • Log Monitoring│
│ • Session Cache │    │ • Chat Endpoints│    │ • Auto Scaling  │
│ • Health Check  │    │ • Request Routing│   │ • Threshold Mgmt│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Service Details

### 1. Redis Service (`services/redis_service.py`)

**Purpose**: Global state management and session caching

**Key Features**:
- ✅ Initializes with default model "large-model"
- ✅ Session selector storage with TTL (1 hour)
- ✅ Model state management
- ✅ Health checking
- ✅ Error handling and logging

**Default Configuration**:
- Host: localhost
- Port: 6379
- Database: 0
- Default model: "large-model"

**Methods**:
- `get_model()` - Get current model
- `set_model(model)` - Update model
- `set_session_selector(session_id, selector)` - Store session routing
- `get_session_selector(session_id)` - Retrieve session routing
- `health_check()` - Check Redis connectivity

### 2. FastAPI Server (`services/api_server.py`)

**Purpose**: REST API for session management and chat completions

**Key Features**:
- ✅ Two main endpoints: `/initiate_call` and `/chat_completions`
- ✅ Session-based routing using Redis
- ✅ Comprehensive logging (console + file)
- ✅ Health check endpoint
- ✅ Error handling and validation

**Endpoints**:
- `POST /initiate_call` - Start new session, assign routing
- `POST /chat_completions` - Process chat requests
- `GET /health` - Service health check

**Logging**:
- Console: Colored, formatted output
- File: `.logs/api_server.log` with rotation

### 3. Capacity Planning Service (`services/capacity_planning_service.py`)

**Purpose**: Automated scaling based on log monitoring

**Key Features**:
- ✅ Monitors `.logs/` directory size every 10 seconds
- ✅ Automatic scale-up when threshold exceeded
- ✅ Automatic scale-down when load decreases
- ✅ Dual-threaded monitoring (scale-up + scale-down)
- ✅ Comprehensive logging

**Scaling Logic**:

**Scale Up** (when log size > threshold):
1. Spin up large model (simulated 3 minutes)
2. Spin up small model (simulated 20 seconds)
3. Update Redis to use small model
4. Double the threshold

**Scale Down** (when log size < initial threshold AND no small model usage):
1. Shut down small model
2. Reset to large model
3. Reset threshold to original value

**Configuration**:
- Check interval: 10 seconds
- Initial threshold: 1MB
- Log directory: `.logs/`

## 🔄 System Flow

### Session Initiation Flow
```
1. Client → POST /initiate_call
2. API Server → Generate session ID + selector
3. API Server → Redis (store session selector)
4. API Server → Client (return session info)
```

### Chat Processing Flow
```
1. Client → POST /chat_completions (with session_id)
2. API Server → Redis (get session selector)
3. API Server → Model selection based on Redis state
4. API Server → Client (return response)
```

### Capacity Planning Flow
```
1. Monitor Thread → Check log directory size
2. If size > threshold → Trigger scale-up
3. Scale-up Thread → Spin up models
4. Scale-up Thread → Update Redis model state
5. Scale-down Thread → Monitor for scale-down conditions
6. Scale-down Thread → Reset to large model when safe
```

## 🚀 Running the System

### Prerequisites
```bash
# Install dependencies
uv sync

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:alpine
```

### Quick Start
```bash
# Run all services
python main.py all

# Or run individually
python main.py redis    # Check Redis
python main.py api      # Start API server
python main.py capacity # Start capacity planning
```

### Testing
```bash
# Test API functionality
python test_system.py

# Demo capacity planning
python demo_capacity_planning.py
```

## 📊 Monitoring and Observability

### Log Files
- `.logs/api_server.log` - API server logs
- `.logs/capacity_planning.log` - Capacity planning logs

### Log Features
- Rotation: 10MB per file
- Retention: 7 days
- Format: Timestamp | Level | Module:Function:Line - Message
- Console: Colored, real-time output

### Health Checks
- Redis connectivity
- API server status
- Capacity planning service status

## 🔧 Configuration

### Redis Service
```python
redis_service = RedisService(
    host="localhost",
    port=6379,
    db=0
)
```

### API Server
```python
# Default: http://localhost:8000
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Capacity Planning Service
```python
service = CapacityPlanningService(
    log_dir=".logs",
    check_interval=10,
    initial_threshold=1024 * 1024,  # 1MB
    api_base_url="http://localhost:8000"
)
```

## 🎯 Design Requirements Met

✅ **Redis Service**: Global session and model state management
✅ **FastAPI Server**: Two endpoints with session routing
✅ **Capacity Planning**: Log monitoring with automatic scaling
✅ **Logging**: Console output + `.logs/` directory storage
✅ **Modular Design**: Separate services that can run independently
✅ **Session Management**: Redis-based session routing
✅ **Auto Scaling**: Threshold-based model switching
✅ **Error Handling**: Comprehensive error handling and logging

## 🔍 Key Implementation Details

### Session Routing
- 4-bit selector (0-15) for routing decisions
- Stored in Redis with 1-hour TTL
- Per-session routing (not per-request)

### Model Switching
- Large model: 3-minute spin-up simulation
- Small model: 20-second spin-up simulation
- Automatic fallback and recovery

### Log Monitoring
- Real-time directory size monitoring
- Configurable thresholds
- Automatic scale-up and scale-down

### Error Resilience
- Redis connection error handling
- API request validation
- Graceful service shutdown

## 🚀 Next Steps

1. **Production Deployment**:
   - Add Docker containers for each service
   - Implement proper Redis clustering
   - Add metrics collection (Datadog integration)

2. **Enhanced Features**:
   - Real LLM model integration
   - Advanced routing algorithms
   - Performance optimization

3. **Monitoring**:
   - Add Prometheus metrics
   - Implement alerting
   - Add distributed tracing

This implementation provides a solid foundation for the LLM fallback routing system as described in the design document, with all three services working together to provide robust, scalable LLM service management. 