"""
Unit tests for Inventory aggregate.
Tests the domain logic in isolation without external dependencies.
"""
import pytest
from src.domain.inventory import Inventory
from src.domain.exceptions import InvalidQuantityError


class TestInventoryCreation:
    """Test Inventory aggregate creation and initialization"""

    def test_create_inventory_with_valid_data(self):
        """T026: Create inventory with valid data"""
        inventory = Inventory(
            product_id="PROD-001",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )

        assert inventory.product_id == "PROD-001"
        assert inventory.total_quantity == 100
        assert inventory.reserved_quantity == 20
        assert inventory.minimum_stock_level == 10

    def test_create_inventory_with_defaults(self):
        """T026: Create inventory with default values"""
        inventory = Inventory(
            product_id="PROD-002",
            total_quantity=50
        )

        assert inventory.product_id == "PROD-002"
        assert inventory.total_quantity == 50
        assert inventory.reserved_quantity == 0
        assert inventory.minimum_stock_level == 0


class TestInventoryInvariants:
    """Test Inventory aggregate invariant validation"""

    def test_negative_total_quantity_raises_error(self):
        """T027: Negative total quantity should raise error"""
        with pytest.raises(InvalidQuantityError, match="Total quantity cannot be negative"):
            Inventory(
                product_id="PROD-003",
                total_quantity=-10
            )

    def test_negative_reserved_quantity_raises_error(self):
        """T027: Negative reserved quantity should raise error"""
        with pytest.raises(InvalidQuantityError, match="Reserved quantity cannot be negative"):
            Inventory(
                product_id="PROD-004",
                total_quantity=100,
                reserved_quantity=-5
            )

    def test_negative_minimum_stock_raises_error(self):
        """T027: Negative minimum stock level should raise error"""
        with pytest.raises(InvalidQuantityError, match="Minimum stock level cannot be negative"):
            Inventory(
                product_id="PROD-005",
                total_quantity=100,
                minimum_stock_level=-1
            )

    def test_reserved_exceeds_total_raises_error(self):
        """T027: Reserved quantity exceeding total should raise error"""
        with pytest.raises(InvalidQuantityError, match="Reserved quantity.*cannot exceed total quantity"):
            Inventory(
                product_id="PROD-006",
                total_quantity=50,
                reserved_quantity=60
            )


class TestAvailableQuantityCalculation:
    """Test available quantity property calculation"""

    def test_available_quantity_with_no_reservations(self):
        """T028: Available quantity equals total when no reservations"""
        inventory = Inventory(
            product_id="PROD-007",
            total_quantity=100,
            reserved_quantity=0
        )

        assert inventory.available_quantity == 100

    def test_available_quantity_with_reservations(self):
        """T028: Available quantity is total minus reserved"""
        inventory = Inventory(
            product_id="PROD-008",
            total_quantity=100,
            reserved_quantity=30
        )

        assert inventory.available_quantity == 70

    def test_available_quantity_when_fully_reserved(self):
        """T028: Available quantity is zero when fully reserved"""
        inventory = Inventory(
            product_id="PROD-009",
            total_quantity=50,
            reserved_quantity=50
        )

        assert inventory.available_quantity == 0
