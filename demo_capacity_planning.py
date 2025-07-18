#!/usr/bin/env python3
"""
Demo script for the Capacity Planning Service.

This script demonstrates how the capacity planning service responds to log size changes.
It artificially increases log file sizes to trigger scaling events.
"""

import os
import time
import threading
from services.capacity_planning_service import CapacityPlanningService
from services.redis_service import redis_service


def create_test_logs(log_dir: str, size_mb: int = 2):
    """Create test log files to trigger capacity planning."""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a large log file
    test_file = os.path.join(log_dir, "test_load.log")
    chunk = "This is a test log entry to simulate high load. " * 100  # ~5KB per line
    
    with open(test_file, 'w') as f:
        for i in range((size_mb * 1024 * 1024) // len(chunk)):
            f.write(f"{chunk}\n")
    
    print(f"✅ Created test log file: {test_file} ({size_mb}MB)")


def remove_test_logs(log_dir: str):
    """Remove test log files."""
    test_file = os.path.join(log_dir, "test_load.log")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"✅ Removed test log file: {test_file}")


def monitor_redis_changes():
    """Monitor Redis for model changes."""
    last_model = None
    while True:
        current_model = redis_service.get_model()
        if current_model != last_model:
            print(f"🔄 Model changed: {last_model} → {current_model}")
            last_model = current_model
        time.sleep(1)


def main():
    """Main demo function."""
    print("🎬 Capacity Planning Service Demo")
    print("=" * 50)
    
    # Check Redis connection
    if not redis_service.health_check():
        print("❌ Redis is not available. Please start Redis first.")
        return
    
    print("✅ Redis connection successful")
    
    # Initialize capacity planning service with lower threshold for demo
    service = CapacityPlanningService(
        initial_threshold=1024 * 100,  # 100KB for demo
        check_interval=5,  # 5 seconds for demo
        capacity_check_time_window=20
    )
    
    # Start monitoring Redis changes in background
    redis_monitor = threading.Thread(target=monitor_redis_changes, daemon=True)
    redis_monitor.start()
    
    # Start capacity planning service
    print("🚀 Starting capacity planning service...")
    service.start()
    
    try:
        # Wait a bit for service to start
        time.sleep(2)
        
        print("\n📊 Current status:")
        status = service.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Phase 1: Create high load
        print("\n🔥 Phase 1: Creating high load (2MB logs)...")
        create_test_logs(".logs", 2)
        
        print("⏳ Waiting for capacity planning to respond...")
        time.sleep(240)  # Wait for service to detect and respond
        # Intermediate status
        print("\n📊 Intermediate status:")
        status = service.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Phase 2: Remove load
        print("\n🧹 Phase 2: Removing load...")
        remove_test_logs(".logs")
        
        """
        # Not in scope of this project, but we can add it later
        print("⏳ Waiting for scale-down...")
        time.sleep(30)  # Wait for scale-down
        """
        # Final status
        print("\n📊 Final status:")
        status = service.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Demo completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    finally:
        # Cleanup
        service.stop()
        remove_test_logs(".logs")
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    main() 