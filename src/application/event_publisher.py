"""
Event publisher interface for domain events.
This abstraction allows the domain layer to emit events without knowing
about the infrastructure (in-memory, message queue, etc.).
"""
from abc import ABC, abstractmethod
from typing import Any


class EventPublisher(ABC):
    """Abstract base class for event publishing"""

    @abstractmethod
    def publish(self, event: Any) -> None:
        """
        Publish a domain event.

        Args:
            event: Domain event to publish (InventoryReserved, InventoryReleased, etc.)
        """
        pass

    @abstractmethod
    def publish_many(self, events: list[Any]) -> None:
        """
        Publish multiple domain events.

        Args:
            events: List of domain events to publish
        """
        pass
