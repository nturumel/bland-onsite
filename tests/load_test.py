#!/usr/bin/env python3
"""
Load Testing Suite for LLM Fallback Routing System

This module implements simple load testing that simulates traffic spikes
by dumping logs and scale-back by removing logs.
"""

import time
import statistics
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
from datetime import datetime


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    start_time: datetime
    end_time: datetime
    model_usage_stats: Dict[str, int]  # Track which models were used


class LoadTester:
    """Load testing framework for the LLM Fallback Routing System."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_ids: List[str] = []
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.model_usage: Dict[str, int] = {"large-model": 0, "small-model": 0}

    def _make_single_request(self, request_number: int) -> Dict[str, Any]:
        """Make a single request: initiate session then chat completion."""
        start_time = time.time()
        
        try:
            # Step 1: Initiate session
            initiate_response = requests.post(
                f"{self.base_url}/initiate_call",
                json={"session_id": f"load-test-{request_number}"},
                timeout=10,
            )
            
            if initiate_response.status_code != 200:
                end_time = time.time()
                return {
                    "success": False,
                    "response_time": end_time - start_time,
                    "status_code": initiate_response.status_code,
                    "error": f"Failed to initiate session: {initiate_response.text}",
                }
            
            session_data = initiate_response.json()
            session_id = session_data["session_id"]
            
            # Step 2: Chat completion with the session
            chat_response = requests.post(
                f"{self.base_url}/chat_completions",
                json={"session_id": session_id, "message": f"Request {request_number}"},
                timeout=30,
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                model_used = data.get("model_used", "unknown")
                self.model_usage[model_used] = self.model_usage.get(model_used, 0) + 1
                
                return {
                    "success": True,
                    "response_time": response_time,
                    "status_code": chat_response.status_code,
                    "data": data,
                    "model_used": model_used,
                    "session_id": session_id,
                }
            else:
                return {
                    "success": False,
                    "response_time": response_time,
                    "status_code": chat_response.status_code,
                    "error": chat_response.text,
                    "session_id": session_id,
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "status_code": None,
                "error": str(e),
            }
    
    def _make_continuous_requests(self, duration: int, requests_per_second: int = 2) -> List[Dict[str, Any]]:
        """Make continuous requests for a specified duration, each request initiates then chats."""
        print(f"🚀 Making continuous requests for {duration}s at {requests_per_second} RPS...")
        print(f"📝 Each request: initiate session → chat completion")
        
        all_results = []
        interval = 1.0 / requests_per_second
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration:
            # Make single request (initiate + chat)
            result = self._make_single_request(request_count + 1)
            all_results.append(result)
            request_count += 1
            
            # Sleep to maintain rate
            time.sleep(interval)
        
        print(f"✅ Completed {len(all_results)} requests (initiate + chat each)")
        return all_results
    
    def _dump_logs(self, num_files: int = 5, file_size_mb: int = 50):
        """Dump large log files to simulate traffic spike."""
        print(f"📊 Dumping {num_files} log files ({file_size_mb}MB each) to simulate traffic spike...")
        
        log_dir = "../.logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create large log files
        for i in range(num_files):
            filename = f"spike_log_{int(time.time())}_{i}.log"
            filepath = os.path.join(log_dir, filename)
            
            # Create file with specified size
            with open(filepath, 'w') as f:
                # Write repeated log entries to reach desired size
                log_entry = f"[{datetime.now()}] INFO - Simulated high traffic log entry for load testing - this is a much longer log entry to create bigger files faster\n"
                entries_needed = (file_size_mb * 1024 * 1024) // len(log_entry)
                
                for j in range(entries_needed):
                    f.write(log_entry)
            
            print(f"📄 Created: {filename} ({file_size_mb}MB)")
    
    def _clear_logs(self):
        """Clear all log files to simulate scale-back."""
        print("🧹 Clearing log files to simulate scale-back...")
        log_dir = "../.logs"
        if os.path.exists(log_dir):
            try:
                deleted_count = 0
                for filename in os.listdir(log_dir):
                    filepath = os.path.join(log_dir, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"🗑️  Deleted: {filename}")
                print(f"✅ Cleared {deleted_count} log files")
            except Exception as e:
                print(f"❌ Error clearing logs: {e}")
        else:
            print("ℹ️  Log directory does not exist")
    
    def _calculate_statistics(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate response time statistics."""
        if not response_times:
            return {"avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0}

        sorted_times = sorted(response_times)
        return {
            "avg": statistics.mean(response_times),
            "min": min(response_times),
            "max": max(response_times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
        }
    
    def _print_results(self, result: LoadTestResult):
        """Print load test results in a formatted way."""
        print(f"\n{'='*60}")
        print(f"LOAD TEST RESULTS: {result.test_name}")
        print(f"{'='*60}")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Error Rate: {result.error_rate:.2%}")
        print(f"Total Time: {result.total_time:.2f}s")
        print(f"Requests/Second: {result.requests_per_second:.2f}")
        print(f"\nResponse Times:")
        print(f"  Average: {result.avg_response_time:.3f}s")
        print(f"  Min: {result.min_response_time:.3f}s")
        print(f"  Max: {result.max_response_time:.3f}s")
        print(f"  95th Percentile: {result.p95_response_time:.3f}s")
        print(f"  99th Percentile: {result.p99_response_time:.3f}s")
        print(f"\nModel Usage:")
        for model, count in result.model_usage_stats.items():
            percentage = (
                (count / result.total_requests * 100)
                if result.total_requests > 0
                else 0
            )
            print(f"  {model}: {count} requests ({percentage:.1f}%)")
        print(f"\nTime Range: {result.start_time} to {result.end_time}")
        print(f"{'='*60}\n")
    
    def simple_load_test(self, duration: int = 300) -> LoadTestResult:
        """
        Simple load test that continuously makes calls while simulating
        traffic spikes with log dumps and scale-back with log removal.
        Each request: initiate session → chat completion.
        """
        print("🚀 Starting Simple Load Test")
        print("=" * 60)
        
        start_time = datetime.now()
        all_response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Phase 1: Normal traffic (30 seconds)
        print(f"\n🔄 Phase 1: Normal Traffic (30s)")
        normal_results = self._make_continuous_requests(30, requests_per_second=2)
        
        for result in normal_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1
        
        print(f"✅ Normal traffic completed: {len(normal_results)} requests")
        
        # Phase 2: Traffic spike simulation (dump logs)
        print(f"\n📈 Phase 2: Traffic Spike Simulation")
        self._dump_logs(num_files=10, file_size_mb=100)  # Much bigger files
        
        # Phase 3: High traffic after spike (60 seconds)
        print(f"\n🔥 Phase 3: High Traffic After Spike (60s)")
        high_results = self._make_continuous_requests(60, requests_per_second=5)
        
        for result in high_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1
        
        print(f"✅ High traffic completed: {len(high_results)} requests")
        
        # Phase 4: Scale-back simulation (clear logs)
        print(f"\n📉 Phase 4: Scale-Back Simulation")
        self._clear_logs()
        
        # Phase 5: Recovery traffic after scale-back (30 seconds)
        print(f"\n🔄 Phase 5: Recovery Traffic After Scale-Back (30s)")
        recovery_results = self._make_continuous_requests(30, requests_per_second=2)
        
        for result in recovery_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1
        
        print(f"✅ Recovery traffic completed: {len(recovery_results)} requests")
        
        # Phase 6: Another spike
        print(f"\n📈 Phase 6: Another Traffic Spike")
        self._dump_logs(num_files=8, file_size_mb=75)  # Another big spike
        
        # Phase 7: Final high traffic after second spike (45 seconds)
        print(f"\n🔥 Phase 7: Final High Traffic After Second Spike (45s)")
        final_results = self._make_continuous_requests(45, requests_per_second=4)
        
        for result in final_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1
        
        print(f"✅ Final high traffic completed: {len(final_results)} requests")
        
        # Phase 8: Final scale-back
        print(f"\n📉 Phase 8: Final Scale-Back")
        self._clear_logs()
        
        # Phase 9: Final recovery (15 seconds)
        print(f"\n🔄 Phase 9: Final Recovery (15s)")
        final_recovery_results = self._make_continuous_requests(15, requests_per_second=1)
        
        for result in final_recovery_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1
        
        print(f"✅ Final recovery completed: {len(final_recovery_results)} requests")
        
        # Calculate final statistics
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        total_requests = len(all_response_times)
        
        stats = self._calculate_statistics(all_response_times)
        
        test_result: LoadTestResult = LoadTestResult(
            test_name=f"Simple Load Test ({total_requests} requests, {total_time:.0f}s)",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=stats["avg"],
            min_response_time=stats["min"],
            max_response_time=stats["max"],
            p95_response_time=stats["p95"],
            p99_response_time=stats["p99"],
            requests_per_second=total_requests / total_time,
            error_rate=failed_requests / total_requests,
            start_time=start_time,
            end_time=end_time,
            model_usage_stats=self.model_usage.copy(),
        )
        
        self._print_results(test_result)
        return test_result

    def save_results(
        self, results: List[LoadTestResult], filename: str = "load_test_results.json"
    ):
        """Save load test results to JSON file."""
        data = []
        for result in results:
            data.append(
                {
                    "test_name": result.test_name,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "total_time": result.total_time,
                    "avg_response_time": result.avg_response_time,
                    "min_response_time": result.min_response_time,
                    "max_response_time": result.max_response_time,
                    "p95_response_time": result.p95_response_time,
                    "p99_response_time": result.p99_response_time,
                    "requests_per_second": result.requests_per_second,
                    "error_rate": result.error_rate,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "model_usage_stats": result.model_usage_stats,
                }
            )

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"📄 Results saved to {filename}")


def main():
    """Main function to run load tests."""
    print("LLM Fallback Routing System - Simple Load Testing")
    print("Make sure all services are running before starting tests")
    print()

    # Check if services are available
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not responding properly")
            return
        print("✅ API server is available")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return

    # Create load tester
    tester = LoadTester()
    results = []

    # Run simple load test
    print("\n" + "=" * 60)
    results.append(tester.simple_load_test())

    # Save results
    tester.save_results(results)

    print("\n🎉 Load testing completed!")
    print("Check the results above and the saved JSON file for detailed analysis.")


if __name__ == "__main__":
    main()
