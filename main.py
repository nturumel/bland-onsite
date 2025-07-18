#!/usr/bin/env python3
"""
Main entry point for the LLM Fallback Routing System.

This script demonstrates how to run all three services:
1. Redis Service (requires Redis server running)
2. FastAPI Server
3. Capacity Planning Service

Usage:
    python main.py [service_name]

Available services:
    - redis: Initialize Redis with default keys
    - api: Start the FastAPI server
    - capacity: Start the capacity planning service
    - all: Start all services (except Redis which needs to be running separately)
"""

import sys
import time
import threading

# Import our services
from services.redis_service import redis_service
from services.api_server import app
from services.capacity_planning_service import capacity_planning_service


def check_redis_connection():
    """Check if Redis is available."""
    try:
        if redis_service.health_check():
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False


def start_api_server():
    """Start the FastAPI server."""
    import uvicorn
    print("🚀 Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


def start_capacity_planning():
    """Start the capacity planning service."""
    print("📊 Starting capacity planning service")
    capacity_planning_service.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        capacity_planning_service.stop()
        print("Capacity planning service stopped")


def run_all_services():
    """Run all services in separate threads."""
    print("🎯 Starting all services...")
    
    # Check Redis first
    if not check_redis_connection():
        print("Please start Redis server first:")
        print("  docker run -d -p 6379:6379 redis:alpine")
        print("  or")
        print("  redis-server")
        return
    
    # Start capacity planning service in a thread
    capacity_thread = threading.Thread(target=start_capacity_planning, daemon=True)
    capacity_thread.start()
    
    # Start API server in main thread
    start_api_server()


def show_usage():
    """Show usage information."""
    print(__doc__)
    print("\nExamples:")
    print("  python main.py redis     # Check Redis connection")
    print("  python main.py api       # Start API server only")
    print("  python main.py capacity  # Start capacity planning only")
    print("  python main.py all       # Start all services")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    service = sys.argv[1].lower()
    
    if service == "redis":
        if check_redis_connection():
            current_model = redis_service.get_model()
            print(f"Current model in Redis: {current_model}")
        else:
            print("Redis is not available. Please start Redis server first.")
    
    elif service == "api":
        start_api_server()
    
    elif service == "capacity":
        start_capacity_planning()
    
    elif service == "all":
        run_all_services()
    
    else:
        print(f"Unknown service: {service}")
        show_usage()


if __name__ == "__main__":
    main()
