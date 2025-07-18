from functools import lru_cache
import os
import time
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
import sys

from .redis_service import redis_service


# Configure logging
def setup_logging():
    """Setup logging to both console and file."""
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

    # Create logs directory if it doesn't exist
    os.makedirs(".logs", exist_ok=True)

    # Add file handler
    logger.add(
        ".logs/api_server_{time:YYYY-MM-DD_HH-mm-ss}.log",
        rotation="1 second",
        retention="1 hour",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}",
        level="INFO",
    )


# Setup logging
setup_logging()


# Pydantic models
class InitiateCallRequest(BaseModel):
    session_id: Optional[str] = None


class InitiateCallResponse(BaseModel):
    session_id: str
    model: str
    status: str


class ChatCompletionRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    session_id: str
    response: str
    model_used: str
    status: str


# FastAPI app
app = FastAPI(title="Data Plane API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting API server...")
    if not redis_service.health_check():
        logger.error("Redis service is not healthy!")
        raise Exception("Redis service unavailable")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_healthy = redis_service.health_check()
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis": "connected" if redis_healthy else "disconnected",
    }


@app.post("/initiate_call", response_model=InitiateCallResponse)
async def initiate_call(request: InitiateCallRequest):
    """Initiate a new session and assign model routing."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Get current model from Redis
        # This is an oversimplification, we would have to track the state of the model and the deployment
        # We would perform some computation to determine with probability to select which model to use
        current_model = redis_service.get_model()
        if not current_model:
            # Log the exception, and revert to a default model
            logger.error("No model found in Redis, using default model")
            current_model = "small-model"

        new_session_id = session_id + "_" + current_model # In actual code we will hash the model and replace the last 4 digits with the hash, This is just a hack to test the code more easily
        # Store session model in Redis
        # Not required in current implementation, can take it out
        if not redis_service.set_session_model(new_session_id, current_model):
            raise HTTPException(
                status_code=500, detail="Failed to store session model"
            )

        logger.info(f"Initiated session {new_session_id} with model {current_model}")

        return InitiateCallResponse(
            session_id=new_session_id, model=current_model, status="initiated"
        )

    except Exception as e:
        logger.error(f"Error in initiate_call: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/chat_completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """Process chat completion request."""
    # Add logs to caclulate the time of the request
    start_time = time.time()
    try:
        # Get the model from the session id
        model_to_use = get_model_from_session_id(request.session_id)
        if not model_to_use:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} does not have a model",
            )

        # Simulate LLM processing based on model
        # Not in scope, but we default to default models, other inference endpoints if we have failures
        # We cache those fallbacks or something, open to suggestions
        if model_to_use == "large-model":
            response_text = f"Large model response for session {request.session_id}: {request.message}"
            # Sleep for 2 seconds
            time.sleep(2)  
        elif model_to_use == "small-model":
            response_text = f"Small model response for session {request.session_id}: {request.message}"
            # Sleep for 1 seconds
            time.sleep(1)
        else:
            response_text = f"Unknown model {model_to_use} response: {request.message}"

        logger.info(
            f"Processed chat completion for session {request.session_id} using {model_to_use}"
        )
        # Add logs to calculate the time of the request
        end_time = time.time()
        logger.info(f"Chat completion for session {request.session_id} took {end_time - start_time} seconds")
        return ChatCompletionResponse(
            session_id=request.session_id,
            response=response_text,
            model_used=model_to_use,
            status="completed",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Helper methods
@lru_cache(maxsize=10)
def get_model_from_session_id(session_id: str) -> str:
    """Get model from session ID."""
    return session_id.split("_")[1]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
