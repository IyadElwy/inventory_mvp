"""
Inventory Aggregate - Domain Model.
Represents the core inventory business logic with validation and invariants.
"""
from dataclasses import dataclass, field
from typing import List, Any
from src.domain.exceptions import InvalidQuantityError


@dataclass
class Inventory:
    """
    Inventory Aggregate Root.

    Manages product inventory with total, reserved, and available quantities.
    Enforces business invariants and emits domain events for state changes.
    """
    product_id: str
    total_quantity: int
    reserved_quantity: int = 0
    minimum_stock_level: int = 0

    def __post_init__(self):
        """Validate business invariants after initialization"""
        self._validate_invariants()

    def _validate_invariants(self):
        """
        Enforce business rules:
        - All quantities must be non-negative
        - Reserved quantity cannot exceed total quantity
        """
        if self.total_quantity < 0:
            raise InvalidQuantityError("Total quantity cannot be negative")

        if self.reserved_quantity < 0:
            raise InvalidQuantityError("Reserved quantity cannot be negative")

        if self.minimum_stock_level < 0:
            raise InvalidQuantityError("Minimum stock level cannot be negative")

        if self.reserved_quantity > self.total_quantity:
            raise InvalidQuantityError(
                f"Reserved quantity ({self.reserved_quantity}) cannot exceed "
                f"total quantity ({self.total_quantity})"
            )

    @property
    def available_quantity(self) -> int:
        """
        Calculate available quantity.
        Available = Total - Reserved
        """
        return self.total_quantity - self.reserved_quantity
