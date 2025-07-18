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

    def _make_request(self, session_id: str, message: str) -> Dict[str, Any]:
        """Make a chat completion request and return timing data."""
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/chat_completions",
                json={"session_id": session_id, "message": message},
                timeout=30,
            )

            end_time = time.time()
            response_time = end_time - start_time

            if response.status_code == 200:
                data = response.json()
                model_used = data.get("model_used", "unknown")
                self.model_usage[model_used] = self.model_usage.get(model_used, 0) + 1

                return {
                    "success": True,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "data": data,
                    "model_used": model_used,
                }
            else:
                return {
                    "success": False,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "error": response.text,
                }

        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "status_code": None,
                "error": str(e),
            }

    def _initiate_sessions(self, num_sessions: int) -> List[str]:
        """Initiate multiple sessions and return session IDs."""
        print(f"🔄 Initiating {num_sessions} new sessions...")
        session_ids = []

        with ThreadPoolExecutor(max_workers=min(num_sessions, 10)) as executor:
            futures = []
            for i in range(num_sessions):
                future = executor.submit(
                    requests.post,
                    f"{self.base_url}/initiate_call",
                    json={
                        "session_id": f"load-test-session-{len(self.session_ids) + i}"
                    },
                    timeout=10,
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    response = future.result()
                    if response.status_code == 200:
                        session_id = response.json()["session_id"]
                        session_ids.append(session_id)
                        print(f"✅ Session initiated: {session_id}")
                    else:
                        print(f"❌ Failed to initiate session: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error initiating session: {e}")

        return session_ids

    def _make_continuous_requests(
        self,
        session_ids: List[str],
        duration: int,
        requests_per_second: int = 2,
        max_requests_per_session: int = 4,
    ) -> List[Dict[str, Any]]:
        """Make continuous requests for a specified duration."""
        print(
            f"🚀 Making continuous requests for {duration}s at {requests_per_second} RPS..."
        )
        print(f"📝 Each session limited to {max_requests_per_session} requests")

        all_results = []
        interval = 1.0 / requests_per_second
        start_time = time.time()
        request_count = 0
        session_request_counts = {session_id: 0 for session_id in session_ids}

        while time.time() - start_time < duration:
            # Find a session that hasn't reached its limit
            available_sessions = [
                sid
                for sid in session_ids
                if session_request_counts[sid] < max_requests_per_session
            ]

            if not available_sessions:
                print(
                    "⚠️  All sessions have reached their request limit, stopping early"
                )
                break

            # Use sessions in round-robin fashion among available ones
            session_id = available_sessions[request_count % len(available_sessions)]
            message = f"Continuous request {request_count + 1} (session {session_id[-10:]} request {session_request_counts[session_id] + 1})"

            result = self._make_request(session_id, message)
            all_results.append(result)
            session_request_counts[session_id] += 1
            request_count += 1

            # Sleep to maintain rate
            time.sleep(interval)

        print(
            f"✅ Completed {len(all_results)} requests across {len(session_ids)} sessions"
        )
        return all_results

    def _dump_logs(self, num_files: int = 5, file_size_mb: int = 50):
        """Dump large log files to simulate traffic spike."""
        print(
            f"📊 Dumping {num_files} log files ({file_size_mb}MB each) to simulate traffic spike..."
        )

        log_dir = "../.logs"
        os.makedirs(log_dir, exist_ok=True)

        # Create large log files
        for i in range(num_files):
            filename = f"spike_log_{int(time.time())}_{i}.log"
            filepath = os.path.join(log_dir, filename)

            # Create file with specified size
            with open(filepath, "w") as f:
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
        """
        print("🚀 Starting Simple Load Test")
        print("=" * 60)

        start_time = datetime.now()
        all_response_times = []
        successful_requests = 0
        failed_requests = 0

        # Phase 1: Initial sessions
        print(f"\n📋 Phase 1: Initial Sessions")
        initial_sessions = self._initiate_sessions(5)
        self.session_ids.extend(initial_sessions)

        # Phase 2: Normal traffic (30 seconds)
        print(f"\n🔄 Phase 2: Normal Traffic (30s)")
        normal_results = self._make_continuous_requests(
            initial_sessions, 30, requests_per_second=2, max_requests_per_session=4
        )

        for result in normal_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

        print(f"✅ Normal traffic completed: {len(normal_results)} requests")

        # Phase 3: Traffic spike simulation (dump logs)
        print(f"\n📈 Phase 3: Traffic Spike Simulation")
        self._dump_logs(num_files=10, file_size_mb=100)  # Much bigger files

        # Phase 4: New sessions after spike
        print(f"\n📋 Phase 4: New Sessions After Spike")
        spike_sessions = self._initiate_sessions(8)
        self.session_ids.extend(spike_sessions)

        # Phase 5: High traffic with new sessions (60 seconds)
        print(f"\n🔥 Phase 5: High Traffic with New Sessions (60s)")
        high_results = self._make_continuous_requests(
            spike_sessions, 60, requests_per_second=5, max_requests_per_session=4
        )

        for result in high_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

        print(f"✅ High traffic completed: {len(high_results)} requests")

        # Phase 6: Scale-back simulation (clear logs)
        print(f"\n📉 Phase 6: Scale-Back Simulation")
        self._clear_logs()

        # Phase 7: New sessions after scale-back
        print(f"\n📋 Phase 7: New Sessions After Scale-Back")
        recovery_sessions = self._initiate_sessions(6)
        self.session_ids.extend(recovery_sessions)

        # Phase 8: Recovery traffic with new sessions (30 seconds)
        print(f"\n🔄 Phase 8: Recovery Traffic with New Sessions (30s)")
        recovery_results = self._make_continuous_requests(
            recovery_sessions, 30, requests_per_second=2, max_requests_per_session=4
        )

        for result in recovery_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

        print(f"✅ Recovery traffic completed: {len(recovery_results)} requests")

        # Phase 9: Another spike
        print(f"\n📈 Phase 9: Another Traffic Spike")
        self._dump_logs(num_files=8, file_size_mb=75)  # Another big spike

        # Phase 10: New sessions after second spike
        print(f"\n📋 Phase 10: New Sessions After Second Spike")
        spike2_sessions = self._initiate_sessions(7)
        self.session_ids.extend(spike2_sessions)

        # Phase 11: Final high traffic with new sessions (45 seconds)
        print(f"\n🔥 Phase 11: Final High Traffic with New Sessions (45s)")
        final_results = self._make_continuous_requests(
            spike2_sessions, 45, requests_per_second=4, max_requests_per_session=4
        )

        for result in final_results:
            all_response_times.append(result["response_time"])
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

        print(f"✅ Final high traffic completed: {len(final_results)} requests")

        # Phase 12: Final scale-back
        print(f"\n📉 Phase 12: Final Scale-Back")
        self._clear_logs()

        # Phase 13: New sessions after final scale-back
        print(f"\n📋 Phase 13: New Sessions After Final Scale-Back")
        final_recovery_sessions = self._initiate_sessions(4)
        self.session_ids.extend(final_recovery_sessions)

        # Phase 14: Final recovery with new sessions (15 seconds)
        print(f"\n🔄 Phase 14: Final Recovery with New Sessions (15s)")
        final_recovery_results = self._make_continuous_requests(
            final_recovery_sessions,
            15,
            requests_per_second=1,
            max_requests_per_session=4,
        )

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
