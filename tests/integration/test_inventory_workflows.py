"""
Integration tests for inventory workflows.
Tests the interaction between application and infrastructure layers.
"""
import pytest
from sqlalchemy.orm import Session
from src.application.inventory_service import InventoryService
from src.infrastructure.database.repository import InventoryRepository
from src.infrastructure.events.local_publisher import LocalEventPublisher
from src.domain.inventory import Inventory
from src.domain.exceptions import InventoryNotFoundError
from src.infrastructure.database.session import get_db


@pytest.fixture
def db_session():
    """Create a test database session"""
    session = next(get_db())
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def repository(db_session):
    """Create repository with test database"""
    return InventoryRepository(db_session)


@pytest.fixture
def event_publisher():
    """Create event publisher"""
    return LocalEventPublisher()


@pytest.fixture
def inventory_service(repository, event_publisher):
    """Create inventory service with dependencies"""
    return InventoryService(repository, event_publisher)


class TestGetInventoryWorkflow:
    """T029: Test querying inventory via service"""

    def test_get_existing_inventory(self, inventory_service, repository):
        """Get inventory for existing product"""
        # Arrange: Create inventory in database
        inventory = Inventory(
            product_id="PROD-TEST-001",
            total_quantity=100,
            reserved_quantity=25,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Query via service
        result = inventory_service.get_inventory("PROD-TEST-001")

        # Assert: Returns correct inventory
        assert result is not None
        assert result.product_id == "PROD-TEST-001"
        assert result.total_quantity == 100
        assert result.reserved_quantity == 25
        assert result.available_quantity == 75
        assert result.minimum_stock_level == 10

    def test_get_nonexistent_inventory_raises_error(self, inventory_service):
        """Get inventory for non-existent product raises error"""
        # Act & Assert: Should raise InventoryNotFoundError
        with pytest.raises(InventoryNotFoundError, match="PROD-NONEXISTENT"):
            inventory_service.get_inventory("PROD-NONEXISTENT")

    def test_get_inventory_calculates_available_correctly(self, inventory_service, repository):
        """Verify available quantity calculation in full workflow"""
        # Arrange: Create inventory with reservations
        inventory = Inventory(
            product_id="PROD-TEST-002",
            total_quantity=200,
            reserved_quantity=50,
            minimum_stock_level=20
        )
        repository.save(inventory)

        # Act: Query via service
        result = inventory_service.get_inventory("PROD-TEST-002")

        # Assert: Available quantity is correct (200 - 50 = 150)
        assert result.available_quantity == 150
