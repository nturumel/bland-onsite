import os
import time
import threading
from loguru import logger
import sys

from .redis_service import redis_service


class CapacityPlanningService:
    def __init__(
        self,
        log_dir: str = ".logs",
        check_interval: int = 10,
        initial_threshold: int = int(1024 * 1024 * 0.5 * 0.5),  # 0.5MB
        api_base_url: str = "http://localhost:8000",
        capacity_check_time_window: int = 5,
    ):
        """
        Initialize capacity planning service.

        Args:
            log_dir: Directory containing log files
            check_interval: Interval in seconds to check log sizes
            initial_threshold: Initial size threshold in bytes
            api_base_url: Base URL for the API server
        """
        self.log_dir = log_dir
        self.check_interval = check_interval
        self.capacity_check_time_window = capacity_check_time_window
        self.initial_threshold = initial_threshold
        self.current_threshold = initial_threshold
        self.api_base_url = api_base_url
        self.running = False
        self.monitor_thread = None
        self.scale_down_thread = None

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for the capacity planning service."""
        # Remove default handler
        logger.remove()

        # Add console handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>",
            level="INFO",
        )

        # Add file handler
        logger.add(
            f"{self.log_dir}/capacity_planning.log",
            rotation="10 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}",
            level="INFO",
        )

    def get_log_directory_size(self) -> int:
        """Get total size of log files within the time window."""
        import time

        total_size = 0
        current_time = time.time()
        window_start = current_time - self.capacity_check_time_window

        try:
            for filename in os.listdir(self.log_dir):
                filepath = os.path.join(self.log_dir, filename)
                if os.path.isfile(filepath):
                    # Check if file was modified within the time window
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime >= window_start:
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"Error calculating log directory size: {e}")
        return total_size

    def check_logs_for_small_model(self) -> bool:
        """Check if logs within time window contain mentions of small model."""
        # This is not in scope of this project, but we can add it later, needed to scale down
        import time

        current_time = time.time()
        window_start = current_time - self.capacity_check_time_window

        try:
            for filename in os.listdir(self.log_dir):
                if filename.endswith(".log"):
                    filepath = os.path.join(self.log_dir, filename)
                    # Check if file was modified within the time window
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime >= window_start:
                        with open(filepath, "r") as f:
                            content = f.read()
                            if "small-model" in content.lower():
                                return True
        except Exception as e:
            logger.error(f"Error checking logs for small model: {e}")
        return False

    def spin_up_large_model(self) -> bool:
        """Simulate spinning up large model (takes 3 minutes)."""
        logger.info("Starting large model spin-up (simulated 3 minutes)...")
        try:
            # Simulate 3-minute spin-up time
            time.sleep(100)  # 100 seconds for demo

            # Update Redis to use large model
            success = redis_service.set_model("large-model")
            logger.info(f"Redis model set to large-model: {success}")
            if success:
                logger.info("Large model spin-up completed successfully")
                # Double the threshold
                self.current_threshold = self.initial_threshold * 2
                logger.info(f"Threshold increased to {self.current_threshold} bytes")
                return True
            else:
                logger.error("Failed to update Redis for large model")
                return False
        except Exception as e:
            logger.error(f"Error during large model spin-up: {e}")
            return False

    def spin_up_small_model(self) -> bool:
        """Simulate spinning up small model (takes 20 seconds)."""
        logger.info("Starting small model spin-up (simulated 20 seconds)...")
        try:
            # Simulate 20-second spin-up time
            time.sleep(20)

            # Update Redis to use small model
            # There are edge cases here, basically we need to make sure that we only set it to small if the large model spin up has not been completed and updated before
            # We will deal with this in the future, for now we will just set it to small
            success = redis_service.set_model("small-model")
            logger.info(f"Redis model set to small-model: {success}")
            if success:
                logger.info("Small model spin-up completed successfully")
                return True
            else:
                logger.error("Failed to update Redis for small model")
                return False
        except Exception as e:
            logger.error(f"Error during small model spin-up: {e}")
            return False

    def scale_down_models(self) -> bool:
        """Simulate scaling down models."""
        logger.info("Scaling down models...")
        try:
            # Simulate scale-down operations
            time.sleep(5)  # Simulate 5 seconds for scale-down

            # Reset to large model
            success = redis_service.set_model("large-model")
            if success:
                # Reset threshold to original value
                self.current_threshold = self.initial_threshold
                logger.info("Models scaled down successfully")
                logger.info(f"Threshold reset to {self.current_threshold} bytes")
                return True
            else:
                logger.error("Failed to update Redis during scale-down")
                return False
        except Exception as e:
            logger.error(f"Error during scale-down: {e}")
            return False

    def monitor_log_sizes(self):
        """Main monitoring loop for log sizes."""
        logger.info(
            f"Starting log size monitoring (threshold: {self.current_threshold} bytes)"
        )

        while self.running:
            try:
                current_size = self.get_log_directory_size()
                logger.info(
                    f"Current log directory size: {current_size} bytes and current threshold: {self.current_threshold}"
                )

                if current_size > self.current_threshold:
                    logger.warning(
                        f"Log size {current_size} exceeds threshold {self.current_threshold}"
                    )

                    # Ideally we would track state in redis.
                    # We also would monitor the state of the request
                    # We would also track something other than the log size to determine if we need to scale up
                    # We also would track and store the entire configuration and update the redis with the state of the models and deployments
                    # Start large model spin-up in a separate thread
                    large_model_thread = threading.Thread(
                        target=self.spin_up_large_model, daemon=True
                    )
                    large_model_thread.start()

                    # Start small model spin-up in a separate thread
                    small_model_thread = threading.Thread(
                        target=self.spin_up_small_model, daemon=True
                    )
                    small_model_thread.start()

                    # Wait for both to complete
                    large_model_thread.join()
                    small_model_thread.join()

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)

    def scale_down_monitor(self):
        """Monitor for scale-down conditions."""
        logger.info("Starting scale-down monitoring")

        while self.running:
            try:
                current_size = self.get_log_directory_size()
                has_small_model = self.check_logs_for_small_model()

                # Scale down if log size is low and no small model usage
                if (
                    current_size < self.initial_threshold
                    and not has_small_model
                    and self.current_threshold > self.initial_threshold
                ):
                    logger.info("Conditions met for scale-down")
                    self.scale_down_models()

                time.sleep(self.check_interval * 2)  # Check every 20 seconds

            except Exception as e:
                logger.error(f"Error in scale-down monitoring: {e}")
                time.sleep(self.check_interval * 2)

    def start(self):
        """Start the capacity planning service."""
        if self.running:
            logger.warning("Capacity planning service is already running")
            return

        self.running = True

        # Start main monitoring thread
        self.monitor_thread = threading.Thread(
            target=self.monitor_log_sizes, daemon=True
        )
        self.monitor_thread.start()

        # Start scale-down monitoring thread, not within the scope of this project
        # We would need to track the state of the request and the model to determine if we need to scale down

        self.scale_down_thread = threading.Thread(
            target=self.scale_down_monitor, daemon=True
        )
        self.scale_down_thread.start()

        logger.info("Capacity planning service started")

    def stop(self):
        """Stop the capacity planning service."""
        self.running = False
        logger.info("Capacity planning service stopped")

    def get_status(self) -> dict:
        """Get current status of the service."""
        return {
            "running": self.running,
            "current_threshold": self.current_threshold,
            "initial_threshold": self.initial_threshold,
            "log_directory_size": self.get_log_directory_size(),
            "has_small_model_usage": self.check_logs_for_small_model(),
        }


# Global instance
capacity_planning_service = CapacityPlanningService()


if __name__ == "__main__":
    service = CapacityPlanningService()
    try:
        service.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
        print("Service stopped by user")
