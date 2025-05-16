"""
Centralized error handling and logging utilities for Google Chat MCP.
"""

import logging
import traceback
from fastapi.responses import JSONResponse

# --- Logging Setup ---
logger = logging.getLogger("google_chat_mcp")
logger.setLevel(logging.INFO)  # Or DEBUG as needed

def log_exception(msg: str, exc: Exception = None, level: int = logging.ERROR):
    """
    Log an exception with optional traceback.
    """
    if exc:
        logger.log(level, f"{msg}: {str(exc)}")
        logger.debug(traceback.format_exc())
    else:
        logger.log(level, msg)

def format_error_response(error: Exception, message: str = "An unexpected error occurred.", status_code: int = 500):
    """
    Format a FastAPI/HTTP JSON error response for API routes.
    """
    error_details = {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "detail": message
    }
    return JSONResponse(status_code=status_code, content=error_details)

class GoogleChatMCPError(Exception):
    """
    Custom exception class for Google Chat MCP errors.
    """
    def __init__(self, message, code=500):
        super().__init__(message)
        self.code = code

# --- Decorator for route exception handling (optional, for FastAPI) ---
def handle_exceptions(func):
    """
    Decorator to wrap FastAPI endpoints for consistent error handling.
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GoogleChatMCPError as gce:
            log_exception("GoogleChatMCPError", gce)
            return format_error_response(gce, message=str(gce), status_code=gce.code)
        except Exception as e:
            log_exception("Unhandled exception in endpoint", e)
            return format_error_response(e)
    return wrapper

