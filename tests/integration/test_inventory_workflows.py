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
from src.domain.exceptions import InventoryNotFoundError, InsufficientStockError, InvalidQuantityError
from src.domain.events import InventoryReserved, InventoryReleased, InventoryAdjusted
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


class TestReleaseInventoryWorkflow:
    """T051: Test releasing reserved inventory via service"""

    def test_release_inventory_success(self, inventory_service, repository, event_publisher):
        """Release reserved inventory successfully and verify state + events"""
        # Arrange: Create inventory with reservations
        inventory = Inventory(
            product_id="PROD-RELEASE-001",
            total_quantity=100,
            reserved_quantity=50,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Release inventory via service
        result = inventory_service.release_inventory("PROD-RELEASE-001", 30, "ORDER-789", "Customer cancellation")

        # Assert: Inventory state updated correctly
        assert result.reserved_quantity == 20
        assert result.available_quantity == 80

        # Assert: Event was published
        assert len(event_publisher.published_events) == 1
        event = event_publisher.published_events[0]
        assert isinstance(event, InventoryReleased)
        assert event.product_id == "PROD-RELEASE-001"
        assert event.quantity == 30

    def test_release_inventory_exceeding_reserved(self, inventory_service, repository):
        """Release quantity exceeding reserved raises error"""
        # Arrange: Create inventory with limited reservations
        inventory = Inventory(
            product_id="PROD-RELEASE-002",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act & Assert: Should raise InvalidQuantityError
        with pytest.raises(InvalidQuantityError, match="Cannot release"):
            inventory_service.release_inventory("PROD-RELEASE-002", 50, "ORDER-999", "Test")

    def test_reserve_then_release_workflow(self, inventory_service, repository, event_publisher):
        """Test complete reserve-then-release workflow"""
        # Arrange: Create inventory
        inventory = Inventory(
            product_id="PROD-WORKFLOW-001",
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )
        repository.save(inventory)
        original_available = inventory.available_quantity

        # Act: Reserve then release
        inventory_service.reserve_inventory("PROD-WORKFLOW-001", 30, "ORDER-123")
        result = inventory_service.release_inventory("PROD-WORKFLOW-001", 30, "ORDER-123", "Order cancelled")

        # Assert: Available quantity returns to original
        assert result.available_quantity == original_available
        assert result.reserved_quantity == 0

        # Assert: Both events were published
        assert len(event_publisher.published_events) == 2
        assert isinstance(event_publisher.published_events[0], InventoryReserved)
        assert isinstance(event_publisher.published_events[1], InventoryReleased)


class TestAdjustInventoryWorkflow:
    """T062: Test adjusting inventory via service"""

    def test_adjust_inventory_increase(self, inventory_service, repository, event_publisher):
        """Adjust inventory upward and verify state + events"""
        # Arrange: Create inventory
        inventory = Inventory(
            product_id="PROD-ADJUST-001",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Adjust inventory via service
        result = inventory_service.adjust_inventory(
            "PROD-ADJUST-001", 150, "Physical count increase", "manager@example.com"
        )

        # Assert: Inventory state updated correctly
        assert result.total_quantity == 150
        assert result.reserved_quantity == 20
        assert result.available_quantity == 130

        # Assert: Event was published
        assert len(event_publisher.published_events) == 1
        event = event_publisher.published_events[0]
        assert isinstance(event, InventoryAdjusted)
        assert event.product_id == "PROD-ADJUST-001"
        assert event.old_quantity == 100
        assert event.new_quantity == 150

    def test_adjust_inventory_decrease(self, inventory_service, repository, event_publisher):
        """Adjust inventory downward within limits"""
        # Arrange: Create inventory
        inventory = Inventory(
            product_id="PROD-ADJUST-002",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Adjust inventory down to 60
        result = inventory_service.adjust_inventory(
            "PROD-ADJUST-002", 60, "Damaged goods removed", "manager@example.com"
        )

        # Assert: Inventory state updated correctly
        assert result.total_quantity == 60
        assert result.reserved_quantity == 20
        assert result.available_quantity == 40

    def test_adjust_inventory_below_reserved_fails(self, inventory_service, repository):
        """Adjust inventory below reserved quantity raises error"""
        # Arrange: Create inventory with high reservations
        inventory = Inventory(
            product_id="PROD-ADJUST-003",
            total_quantity=100,
            reserved_quantity=80,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act & Assert: Should raise InvalidQuantityError
        with pytest.raises(InvalidQuantityError, match="cannot be less than reserved"):
            inventory_service.adjust_inventory(
                "PROD-ADJUST-003", 50, "Invalid adjustment", "manager@example.com"
            )
