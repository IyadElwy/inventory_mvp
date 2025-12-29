"""
StockLevelMonitor Policy.
Detects low stock conditions and emits alerts.
"""
from typing import List
from src.domain.inventory import Inventory
from src.domain.events import InventoryReserved, InventoryAdjusted, LowStockDetected


class StockLevelMonitor:
    """
    Policy that monitors inventory levels and emits low stock alerts.

    Reacts to InventoryReserved and InventoryAdjusted events to determine
    if available quantity has fallen below minimum stock level.
    """

    def apply(self, event, inventory: Inventory) -> List[LowStockDetected]:
        """
        Apply policy logic to check for low stock condition.

        Args:
            event: The triggering event (InventoryReserved or InventoryAdjusted)
            inventory: Current inventory state after event

        Returns:
            List of LowStockDetected events (empty if not below minimum)
        """
        # Only react to reservation and adjustment events
        if not isinstance(event, (InventoryReserved, InventoryAdjusted)):
            return []

        # Check if available quantity is below minimum threshold
        if inventory.available_quantity < inventory.minimum_stock_level:
            return [LowStockDetected(
                product_id=inventory.product_id,
                available_quantity=inventory.available_quantity,
                minimum_stock_level=inventory.minimum_stock_level
            )]

        return []
