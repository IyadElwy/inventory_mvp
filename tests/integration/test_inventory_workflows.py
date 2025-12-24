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
from src.domain.exceptions import InventoryNotFoundError, InsufficientStockError
from src.domain.events import InventoryReserved
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


class TestReserveInventoryWorkflow:
    """T040: Test reserving inventory via service with event emission"""

    def test_reserve_inventory_success(self, inventory_service, repository, event_publisher):
        """Reserve inventory successfully and verify state + events"""
        # Arrange: Create inventory in database
        inventory = Inventory(
            product_id="PROD-RESERVE-001",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Reserve inventory via service
        result = inventory_service.reserve_inventory("PROD-RESERVE-001", 30, "ORDER-123")

        # Assert: Inventory state updated correctly
        assert result.reserved_quantity == 50
        assert result.available_quantity == 50

        # Assert: Event was published
        assert len(event_publisher.published_events) == 1
        event = event_publisher.published_events[0]
        assert isinstance(event, InventoryReserved)
        assert event.product_id == "PROD-RESERVE-001"
        assert event.quantity == 30

    def test_reserve_inventory_insufficient_stock(self, inventory_service, repository):
        """Reserve inventory with insufficient stock raises error"""
        # Arrange: Create inventory with limited stock
        inventory = Inventory(
            product_id="PROD-RESERVE-002",
            total_quantity=100,
            reserved_quantity=95,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act & Assert: Should raise InsufficientStockError
        with pytest.raises(InsufficientStockError, match="PROD-RESERVE-002"):
            inventory_service.reserve_inventory("PROD-RESERVE-002", 10, "ORDER-456")
