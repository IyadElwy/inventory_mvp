"""
Inventory Application Service.
Orchestrates use cases and coordinates between domain and infrastructure layers.
"""
import logging
from src.domain.inventory import Inventory
from src.domain.exceptions import InventoryNotFoundError
from src.infrastructure.database.repository import InventoryRepository
from src.application.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Application service for inventory use cases.
    Handles business workflows and coordinates persistence/events.
    """

    def __init__(self, repository: InventoryRepository, event_publisher: EventPublisher):
        """
        Initialize service with dependencies.

        Args:
            repository: Repository for inventory persistence
            event_publisher: Publisher for domain events
        """
        self.repository = repository
        self.event_publisher = event_publisher

    def get_inventory(self, product_id: str) -> Inventory:
        """
        Retrieve inventory for a product.

        Args:
            product_id: Product identifier

        Returns:
            Inventory aggregate with current status

        Raises:
            InventoryNotFoundError: If product not found
        """
        logger.info(f"Getting inventory for product: {product_id}")

        inventory = self.repository.get(product_id)

        if inventory is None:
            logger.warning(f"Product not found: {product_id}")
            raise InventoryNotFoundError(f"Product {product_id} not found in inventory")

        logger.info(f"Found inventory for {product_id}: available={inventory.available_quantity}")
        return inventory
