"""
API middleware for cross-cutting concerns.
Includes request ID tracking, logging, and error handling.
"""
import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request for tracing.

    Adds X-Request-ID header to response and logs request/response.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with unique ID tracking.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        try:
            # Process request
            response: Response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Response {request_id}: {response.status_code} ({duration:.3f}s)",
                extra={"request_id": request_id, "duration": duration}
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Error {request_id}: {str(e)} ({duration:.3f}s)",
                exc_info=True,
                extra={"request_id": request_id, "duration": duration}
            )
            raise


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.

    Logs method, path, query params, status code, and duration.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Log request and response details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response object
        """
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Start timing
        start_time = time.time()

        # Log request
        logger.debug(
            f"Request: {method} {path}",
            extra={"method": method, "path": path, "query_params": query_params}
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.debug(
            f"Response: {response.status_code} in {duration:.3f}s",
            extra={
                "status_code": response.status_code,
                "duration": duration,
                "method": method,
                "path": path
            }
        )

        return response
