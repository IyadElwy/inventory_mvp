"""
FastAPI application entry point.
Initializes the app, middleware, and routes using Pydantic Settings.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from src.infrastructure.config import settings

# Configure logging from settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup: Initialize database
    logger.info("Starting up application...")
    from src.infrastructure.database.init_db import init_db
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown: Cleanup if needed
    logger.info("Shutting down application...")


# Create FastAPI app using settings
app = FastAPI(
    title=settings.APP_NAME,
    description="REST API for managing inventory reservations, releases, and adjustments",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS.split(","),
    allow_headers=settings.CORS_ALLOW_HEADERS.split(","),
)

# Add request ID tracking middleware
from src.infrastructure.api.middleware import RequestIDMiddleware, LoggingMiddleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy", "service": "inventory-api"}


# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with API information"""
    return {
        "service": "Inventory Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# Include API routers
from src.infrastructure.api.routes import router
app.include_router(router)
