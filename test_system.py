#!/usr/bin/env python3
"""
Test script to demonstrate the LLM Fallback Routing System.

This script tests the basic functionality of all three services.
Make sure Redis is running and the API server is started before running this script.
"""

import requests


class SystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None

    def test_health(self) -> bool:
        """Test the health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_initiate_call(self) -> bool:
        """Test session initiation."""
        try:
            response = requests.post(
                f"{self.base_url}/initiate_call",
                json={"session_id": None},  # Let server generate session ID
            )
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"✅ Session initiated: {data}")
                return True
            else:
                print(f"❌ Session initiation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Session initiation error: {e}")
            return False

    def test_chat_completion(self, message: str) -> bool:
        """Test chat completion."""
        if not self.session_id:
            print("❌ No session ID available")
            return False

        try:
            response = requests.post(
                f"{self.base_url}/chat_completions",
                json={"session_id": self.session_id, "message": message},
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chat completion: {data}")
                return True
            else:
                print(f"❌ Chat completion failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chat completion error: {e}")
            return False

    def test_multiple_sessions(self) -> bool:
        """Test multiple concurrent sessions."""
        try:
            # Create multiple sessions
            sessions = []
            for i in range(3):
                response = requests.post(
                    f"{self.base_url}/initiate_call",
                    json={"session_id": f"test-session-{i}"},
                )
                if response.status_code == 200:
                    sessions.append(response.json()["session_id"])
                    print(f"✅ Created session {i}: {sessions[-1]}")
                else:
                    print(f"❌ Failed to create session {i}")
                    return False

            # Send messages to each session
            for i, session_id in enumerate(sessions):
                response = requests.post(
                    f"{self.base_url}/chat_completions",
                    json={
                        "session_id": session_id,
                        "message": f"Message from session {i}",
                    },
                )
                if response.status_code == 200:
                    print(f"✅ Session {i} message processed")
                else:
                    print(f"❌ Session {i} message failed")
                    return False

            return True
        except Exception as e:
            print(f"❌ Multiple sessions test error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests."""
        print("🧪 Starting system tests...")
        print("=" * 50)

        tests = [
            ("Health Check", self.test_health),
            ("Session Initiation", self.test_initiate_call),
            ("Chat Completion", lambda: self.test_chat_completion("Hello, world!")),
            ("Multiple Sessions", self.test_multiple_sessions),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! System is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs for details.")


def main():
    """Main test function."""
    print("LLM Fallback Routing System - Test Suite")
    print("Make sure Redis is running and API server is started on localhost:8000")
    print()

    tester = SystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
