"""
FastAPI application entry point.
Initializes the app, middleware, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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


# Create FastAPI app
app = FastAPI(
    title="Inventory Management API",
    description="REST API for managing inventory reservations, releases, and adjustments",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
