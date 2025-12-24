"""
Local in-memory event publisher implementation.
For MVP, events are published synchronously within the same request.
Can be replaced with async message queue publisher (RabbitMQ, Kafka) later.
"""
import logging
from typing import Any
from src.application.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class LocalEventPublisher(EventPublisher):
    """In-memory event publisher for synchronous event handling"""

    def __init__(self):
        self.published_events: list[Any] = []

    def publish(self, event: Any) -> None:
        """
        Publish a single event (stores in memory for MVP).

        Args:
            event: Domain event to publish
        """
        self.published_events.append(event)
        logger.info(f"Published event: {event.__class__.__name__} for product {getattr(event, 'product_id', 'unknown')}")

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
