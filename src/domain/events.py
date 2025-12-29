"""
Domain events for inventory management.
All events are immutable records of state changes.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class InventoryEvent(Protocol):
    """Base protocol for all inventory events"""
    product_id: str
    timestamp: datetime


@dataclass(frozen=True)
class InventoryReserved:
    """Event: Inventory successfully reserved"""
    product_id: str
    quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class InventoryReleased:
    """Event: Reserved inventory released back to available"""
    product_id: str
    quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class InventoryAdjusted:
    """Event: Inventory manually adjusted"""
    product_id: str
    old_quantity: int
    new_quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class LowStockDetected:
    """Event: Inventory fell below minimum threshold"""
    product_id: str
    available_quantity: int
    minimum_stock_level: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class InventoryCreated:
    """Event: New inventory record successfully created"""
    product_id: str
    initial_quantity: int
    minimum_stock_level: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
