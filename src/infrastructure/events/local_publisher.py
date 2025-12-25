"""
Local in-memory event publisher implementation with database persistence.
For MVP, events are published synchronously within the same request.
Can be replaced with async message queue publisher (RabbitMQ, Kafka) later.
"""
import logging
import json
from typing import Any, Optional
from dataclasses import asdict
from src.application.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class LocalEventPublisher(EventPublisher):
    """In-memory event publisher for synchronous event handling with optional persistence"""

    def __init__(self, db_session=None):
        self.published_events: list[Any] = []
        self.db_session = db_session

    def publish(self, event: Any) -> None:
        """
        Publish a single event (stores in memory and optionally persists to database).

        Args:
            event: Domain event to publish
        """
        self.published_events.append(event)
        logger.info(f"Published event: {event.__class__.__name__} for product {getattr(event, 'product_id', 'unknown')}")

        # Persist event to database if session is available
        if self.db_session is not None:
            self._persist_event(event)

    def _persist_event(self, event: Any) -> None:
        """
        Persist event to event_log table for audit trail.

        Args:
            event: Domain event to persist
        """
        try:
            from src.infrastructure.database.models import EventLogModel

            # Convert event to JSON
            event_data = asdict(event) if hasattr(event, '__dataclass_fields__') else {
                'product_id': getattr(event, 'product_id', None),
                'quantity': getattr(event, 'quantity', None),
                'old_quantity': getattr(event, 'old_quantity', None),
                'new_quantity': getattr(event, 'new_quantity', None),
                'available_quantity': getattr(event, 'available_quantity', None),
                'minimum_stock_level': getattr(event, 'minimum_stock_level', None)
            }

            event_log = EventLogModel(
                event_type=event.__class__.__name__,
                product_id=getattr(event, 'product_id', 'unknown'),
                event_data=json.dumps(event_data)
            )

            self.db_session.add(event_log)
            # Note: Session commit is handled by the repository/service layer

            logger.debug(f"Persisted event {event.__class__.__name__} to event_log")
        except Exception as e:
            logger.error(f"Failed to persist event {event.__class__.__name__}: {e}")

    def publish_many(self, events: list[Any]) -> None:
        """
        Publish multiple events.

        Args:
            events: List of domain events to publish
        """
        for event in events:
            self.publish(event)

    def clear(self) -> None:
        """Clear published events (useful for testing)"""
        self.published_events.clear()

    def get_published_events(self) -> list[Any]:
        """Get all published events (useful for testing)"""
        return self.published_events.copy()
