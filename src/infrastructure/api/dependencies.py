"""
Dependency injection helpers for FastAPI routes.
Provides database sessions, repositories, and event publishers.
"""
from typing import Generator
from sqlalchemy.orm import Session
from src.infrastructure.database.session import get_db
from src.infrastructure.database.repository import InventoryRepository
from src.infrastructure.events.local_publisher import LocalEventPublisher
from src.application.event_publisher import EventPublisher


def get_repository(db: Session = None) -> InventoryRepository:
    """
    Get inventory repository with database session.

    Usage in FastAPI:
        @app.get("/inventory/{product_id}")
        def get_inventory(
            product_id: str,
            repo: InventoryRepository = Depends(get_repository)
        ):
            ...
    """
    if db is None:
        # For dependency injection, FastAPI will provide db
        # This is a factory function that FastAPI calls
        from fastapi import Depends
        def _get_repo(session: Session = Depends(get_db)) -> InventoryRepository:
            return InventoryRepository(session)
        return _get_repo
    else:
        # Direct usage (for testing)
        return InventoryRepository(db)


def get_event_publisher() -> EventPublisher:
    """
    Get event publisher instance.

    Usage in FastAPI:
        @app.post("/inventory/{product_id}/reserve")
        def reserve_inventory(
            product_id: str,
            publisher: EventPublisher = Depends(get_event_publisher)
        ):
            ...
    """
    return LocalEventPublisher()


# Convenience functions for FastAPI Depends()
from fastapi import Depends


def get_repo_dependency() -> Generator[InventoryRepository, None, None]:
    """
    FastAPI dependency for repository injection.

    Usage:
        repo: InventoryRepository = Depends(get_repo_dependency)
    """
    db = next(get_db())
    try:
        yield InventoryRepository(db)
    finally:
        db.close()
