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

    def reserve_inventory(self, product_id: str, quantity: int, order_id: str) -> Inventory:
        """
        Reserve inventory for an order atomically.

        Args:
            product_id: Product identifier
            quantity: Quantity to reserve
            order_id: Order ID for idempotency

        Returns:
            Updated inventory aggregate

        Raises:
            InventoryNotFoundError: If product not found
            InsufficientStockError: If not enough available stock
            InvalidQuantityError: If quantity is invalid
        """
        logger.info(f"Reserving {quantity} units of {product_id} for order {order_id}")

        # Get inventory with row lock to prevent concurrent modifications
        inventory = self.repository.get(product_id, for_update=True)

        if inventory is None:
            logger.warning(f"Product not found: {product_id}")
            raise InventoryNotFoundError(f"Product {product_id} not found in inventory")

        # Call domain method to reserve (validates and emits events)
        events = inventory.reserve(quantity)

        # Persist changes
        self.repository.save(inventory)

        # Publish events
        for event in events:
            self.event_publisher.publish(event)

        logger.info(
            f"Reserved {quantity} units of {product_id}. "
            f"New reserved: {inventory.reserved_quantity}, available: {inventory.available_quantity}"
        )

        return inventory

    def release_inventory(self, product_id: str, quantity: int, order_id: str, reason: str) -> Inventory:
        """
        Release reserved inventory back to available pool.

        Args:
            product_id: Product identifier
            quantity: Quantity to release
            order_id: Order ID for tracking
            reason: Reason for release (e.g., "Customer cancellation")

        Returns:
            Updated inventory aggregate

        Raises:
            InventoryNotFoundError: If product not found
            InvalidQuantityError: If quantity is invalid or exceeds reserved
        """
        logger.info(f"Releasing {quantity} units of {product_id} for order {order_id}. Reason: {reason}")

        # Get inventory with row lock to prevent concurrent modifications
        inventory = self.repository.get(product_id, for_update=True)

        if inventory is None:
            logger.warning(f"Product not found: {product_id}")
            raise InventoryNotFoundError(f"Product {product_id} not found in inventory")

        # Call domain method to release (validates and emits events)
        events = inventory.release(quantity)

        # Persist changes
        self.repository.save(inventory)

        # Publish events
        for event in events:
            self.event_publisher.publish(event)

        logger.info(
            f"Released {quantity} units of {product_id}. "
            f"New reserved: {inventory.reserved_quantity}, available: {inventory.available_quantity}"
        )

        return inventory

    def adjust_inventory(self, product_id: str, new_quantity: int, reason: str, adjusted_by: str) -> Inventory:
        """
        Adjust total inventory quantity for physical stock counts.

        Args:
            product_id: Product identifier
            new_quantity: New total quantity
            reason: Reason for adjustment
            adjusted_by: User or system performing adjustment

        Returns:
            Updated inventory aggregate

        Raises:
            InventoryNotFoundError: If product not found
            InvalidQuantityError: If new quantity is invalid
        """
        logger.info(f"Adjusting {product_id} to {new_quantity}. Reason: {reason}, By: {adjusted_by}")

        # Get inventory with row lock to prevent concurrent modifications
        inventory = self.repository.get(product_id, for_update=True)

        if inventory is None:
            logger.warning(f"Product not found: {product_id}")
            raise InventoryNotFoundError(f"Product {product_id} not found in inventory")

        # Call domain method to adjust (validates and emits events)
        events = inventory.adjust(new_quantity, reason, adjusted_by)

        # Persist changes
        self.repository.save(inventory)

        # Publish events
        for event in events:
            self.event_publisher.publish(event)

        logger.info(
            f"Adjusted {product_id} from {events[0].old_quantity} to {new_quantity}. "
            f"New available: {inventory.available_quantity}"
        )

        return inventory

    def get_low_stock_items(self) -> list[Inventory]:
        """
        Query all products with stock below minimum threshold.

        Returns:
            List of Inventory aggregates below minimum stock level
        """
        logger.info("Querying low stock items")

        low_stock_items = self.repository.find_low_stock()

        logger.info(f"Found {len(low_stock_items)} products with low stock")

        return low_stock_items
