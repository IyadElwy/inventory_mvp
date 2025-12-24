"""
Repository pattern for Inventory aggregate.
Provides database abstraction for the domain layer.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.inventory import Inventory
from src.domain.exceptions import InventoryNotFoundError
from src.infrastructure.database.models import InventoryModel


class InventoryRepository:
    """Repository for Inventory aggregate with database persistence"""

    def __init__(self, db: Session):
        self.db = db

    def get(self, product_id: str, for_update: bool = False) -> Optional[Inventory]:
        """
        Retrieve inventory by product ID.

        Args:
            product_id: Product identifier
            for_update: If True, lock row with SELECT FOR UPDATE (prevents concurrent modifications)

        Returns:
            Inventory aggregate or None if not found

        Raises:
            InventoryNotFoundError: If product not found and for_update=True
        """
        query = self.db.query(InventoryModel).filter_by(product_id=product_id)

        if for_update:
            # Use SELECT FOR UPDATE to lock row during transaction
            query = query.with_for_update()

        model = query.first()

        if model is None:
            if for_update:
                raise InventoryNotFoundError(f"Product {product_id} not found in inventory")
            return None

        return model.to_domain()

    def save(self, inventory: Inventory) -> None:
        """
        Save inventory aggregate to database.
        Creates new record if product doesn't exist, updates otherwise.

        Args:
            inventory: Inventory aggregate to persist
        """
        existing = self.db.query(InventoryModel).filter_by(product_id=inventory.product_id).first()

        if existing:
            # Update existing record
            existing.total_quantity = inventory.total_quantity
            existing.reserved_quantity = inventory.reserved_quantity
            existing.minimum_stock_level = inventory.minimum_stock_level
        else:
            # Create new record
            model = InventoryModel.from_domain(inventory)
            self.db.add(model)

        self.db.commit()

    def find_low_stock(self) -> List[Inventory]:
        """
        Find all products with available quantity below minimum stock level.

        Returns:
            List of Inventory aggregates with low stock
        """
        # Query: available_quantity < minimum_stock_level
        # WHERE (total_quantity - reserved_quantity) < minimum_stock_level
        models = self.db.query(InventoryModel).filter(
            (InventoryModel.total_quantity - InventoryModel.reserved_quantity) < InventoryModel.minimum_stock_level
        ).all()

        return [model.to_domain() for model in models]

    def delete(self, product_id: str) -> None:
        """
        Delete inventory record (use with caution).

        Args:
            product_id: Product identifier
        """
        self.db.query(InventoryModel).filter_by(product_id=product_id).delete()
        self.db.commit()
