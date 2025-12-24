"""
Domain commands for inventory management.
Commands represent user intent and are immutable.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ReserveInventory:
    """Command to reserve inventory for an order"""
    product_id: str
    quantity: int
    order_id: str  # For idempotency tracking
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ReleaseInventory:
    """Command to release reserved inventory"""
    product_id: str
    quantity: int
    order_id: str
    reason: str  # e.g., "order_cancelled", "payment_failed"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AdjustInventory:
    """Command to manually adjust inventory"""
    product_id: str
    new_quantity: int
    reason: str  # e.g., "physical_count", "damaged_goods"
    adjusted_by: str  # User or system ID
    timestamp: datetime = field(default_factory=datetime.utcnow)
