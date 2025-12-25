"""
Inventory Aggregate - Domain Model.
Represents the core inventory business logic with validation and invariants.
"""
from dataclasses import dataclass, field
from typing import List, Any
from src.domain.exceptions import InvalidQuantityError, InsufficientStockError
from src.domain.events import InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected


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

    def reserve(self, quantity: int) -> List[Any]:
        """
        Reserve inventory for an order.

        Args:
            quantity: Amount to reserve (must be positive)

        Returns:
            List of domain events emitted

        Raises:
            InvalidQuantityError: If quantity is not positive
            InsufficientStockError: If not enough available stock
        """
        # Validate quantity
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")

        # Check available stock
        if quantity > self.available_quantity:
            raise InsufficientStockError(
                f"Cannot reserve {quantity} units of product {self.product_id}. "
                f"Only {self.available_quantity} available."
            )

        # Update reserved quantity
        self.reserved_quantity += quantity

        # Re-validate invariants after mutation
        self._validate_invariants()

        # Emit domain event
        events = [InventoryReserved(
            product_id=self.product_id,
            quantity=quantity
        )]

        # Check for low stock condition after reservation
        if self.available_quantity < self.minimum_stock_level:
            events.append(LowStockDetected(
                product_id=self.product_id,
                available_quantity=self.available_quantity,
                minimum_stock_level=self.minimum_stock_level
            ))

        return events

    def release(self, quantity: int) -> List[Any]:
        """
        Release reserved inventory back to available pool.

        Args:
            quantity: Amount to release (must be positive)

        Returns:
            List of domain events emitted

        Raises:
            InvalidQuantityError: If quantity is not positive or exceeds reserved
        """
        # Validate quantity
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")

        # Check against reserved quantity
        if quantity > self.reserved_quantity:
            raise InvalidQuantityError(
                f"Cannot release {quantity} units of product {self.product_id}. "
                f"Only {self.reserved_quantity} reserved."
            )

        # Update reserved quantity
        self.reserved_quantity -= quantity

        # Re-validate invariants after mutation
        self._validate_invariants()

        # Emit domain event
        event = InventoryReleased(
            product_id=self.product_id,
            quantity=quantity
        )

        return [event]

    def adjust(self, new_total_quantity: int, reason: str, adjusted_by: str) -> List[Any]:
        """
        Adjust total inventory quantity for physical stock counts.

        Args:
            new_total_quantity: New total quantity
            reason: Reason for adjustment (e.g., "Physical count")
            adjusted_by: User/system performing adjustment

        Returns:
            List of domain events emitted

        Raises:
            InvalidQuantityError: If new total is invalid or less than reserved
        """
        # Validate new total
        if new_total_quantity < 0:
            raise InvalidQuantityError("Total quantity cannot be negative")

        # Check that new total >= reserved
        if new_total_quantity < self.reserved_quantity:
            raise InvalidQuantityError(
                f"New total quantity ({new_total_quantity}) cannot be less than "
                f"reserved quantity ({self.reserved_quantity})"
            )

        # Store old quantity for event
        old_quantity = self.total_quantity

        # Update total quantity
        self.total_quantity = new_total_quantity

        # Re-validate invariants after mutation
        self._validate_invariants()

        # Emit domain event
        events = [InventoryAdjusted(
            product_id=self.product_id,
            old_quantity=old_quantity,
            new_quantity=new_total_quantity
        )]

        # Check for low stock condition after adjustment
        if self.available_quantity < self.minimum_stock_level:
            events.append(LowStockDetected(
                product_id=self.product_id,
                available_quantity=self.available_quantity,
                minimum_stock_level=self.minimum_stock_level
            ))

        return events
