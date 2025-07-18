import time
import redis
import logging
from typing import Optional


class RedisService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis service with connection to Redis server."""
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, decode_responses=True
        )
        self._initialize_default_keys()

    def _initialize_default_keys(self):
        """Initialize default keys in Redis."""
        try:
            # Set default model to 'large-model' if it doesn't exist
            if not self.redis_client.exists("model"):
                self.redis_client.set("model", "large-model")
                logging.info("Initialized Redis with default model: large-model")
            else:
                current_model = self.redis_client.get("model")
                logging.info(f"Redis model key already exists: {current_model}")
        except Exception as e:
            logging.error(f"Failed to initialize Redis keys: {e}")
            raise

    def get_model(self) -> Optional[str]:
        """Get the current model from Redis."""
        try:
            return self.redis_client.get("model")
        except Exception as e:
            logging.error(f"Failed to get model from Redis: {e}")
            return None

    def set_model(self, model: str) -> bool:
        """Set the model in Redis."""
        try:
            self.redis_client.set("model", model)
            logging.info(f"Updated Redis model to: {model}")
            return True
        except Exception as e:
            logging.error(f"Failed to set model in Redis: {e}")
            return False

    def set_session_model(self, session_id: str, model: str) -> bool:
        """Set session selector in Redis."""
        try:
            key = f"session:{session_id}"
            self.redis_client.set(key, model, ex=3600)  # 1 hour TTL
            logging.info(f"Set session model for {session_id}: {model}")
            return True
        except Exception as e:
            logging.error(f"Failed to set session model: {e}")
            return False

    def get_session_model(self, session_id: str) -> Optional[str]:
        """Get session selector from Redis."""
        try:
            key = f"session:{session_id}"
            return self.redis_client.get(key)
        except Exception as e:
            logging.error(f"Failed to get session model: {e}")
            return None

    def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logging.error(f"Redis health check failed: {e}")
            return False


# Global Redis service instance
# Better to implement as a singleton, hacky for now
redis_service = RedisService()


if __name__ == "__main__":
    """
    redis_service = RedisService()
    print(redis_service.get_model())
    print(redis_service.set_model("small-model"))
    print(redis_service.get_model())
    print(redis_service.set_session_model("123", "small-model"))
    print(redis_service.get_session_model("123"))
    print(redis_service.health_check())
    # wait and then clean up
    time.sleep(10)
    redis_service.redis_client.flushall()
    """