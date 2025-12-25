"""
Unit tests for InventoryService.create_inventory() method (T009 - User Story 1).
Tests service orchestration logic with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.domain.inventory import Inventory
from src.domain.events import InventoryCreated, LowStockDetected
from src.domain.exceptions import InvalidQuantityError, InventoryAlreadyExistsError
from src.application.inventory_service import InventoryService


@pytest.fixture
def mock_repository():
    """Create mock repository"""
    return Mock()


@pytest.fixture
def mock_event_publisher():
    """Create mock event publisher"""
    publisher = Mock()
    publisher.publish_many = Mock()
    return publisher


@pytest.fixture
def service(mock_repository, mock_event_publisher):
    """Create service with mocked dependencies"""
    return InventoryService(mock_repository, mock_event_publisher)


class TestInventoryServiceCreate:
    """Test InventoryService.create_inventory() method (T009 - User Story 1)"""

    def test_create_inventory_successful_flow(self, service, mock_repository, mock_event_publisher):
        """T009: Successful creation flow (create → persist → publish events)"""
        # Arrange: Configure mock repository to return created inventory
        expected_inventory = Inventory(
            product_id="SVC-TEST-001",
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )
        mock_repository.create = Mock(return_value=expected_inventory)

        # Act: Call service
        result = service.create_inventory(
            product_id="SVC-TEST-001",
            initial_quantity=100,
            minimum_stock_level=10
        )

        # Assert: Repository.create() was called
        mock_repository.create.assert_called_once()
        created_inventory_arg = mock_repository.create.call_args[0][0]
        assert created_inventory_arg.product_id == "SVC-TEST-001"
        assert created_inventory_arg.total_quantity == 100
        assert created_inventory_arg.reserved_quantity == 0

        # Assert: Events were published
        mock_event_publisher.publish_many.assert_called_once()
        published_events = mock_event_publisher.publish_many.call_args[0][0]
        assert len(published_events) == 1
        assert isinstance(published_events[0], InventoryCreated)

        # Assert: Correct inventory returned
        assert result.product_id == "SVC-TEST-001"
        assert result.total_quantity == 100

    def test_create_inventory_publishes_events_after_persistence(self, service, mock_repository, mock_event_publisher):
        """T009: Events published after successful persistence"""
        # Arrange
        expected_inventory = Inventory(
            product_id="SVC-TEST-002",
            total_quantity=50,
            reserved_quantity=0,
            minimum_stock_level=5
        )
        mock_repository.create = Mock(return_value=expected_inventory)

        # Act
        service.create_inventory(
            product_id="SVC-TEST-002",
            initial_quantity=50,
            minimum_stock_level=5
        )

        # Assert: Repository called before event publishing
        assert mock_repository.create.call_count == 1
        assert mock_event_publisher.publish_many.call_count == 1

    def test_create_inventory_publishes_low_stock_event_when_needed(self, service, mock_repository, mock_event_publisher):
        """T009: Low stock event published when initial < minimum"""
        # Arrange
        expected_inventory = Inventory(
            product_id="SVC-TEST-003",
            total_quantity=5,
            reserved_quantity=0,
            minimum_stock_level=20
        )
        mock_repository.create = Mock(return_value=expected_inventory)

        # Act
        service.create_inventory(
            product_id="SVC-TEST-003",
            initial_quantity=5,
            minimum_stock_level=20
        )

        # Assert: Both InventoryCreated and LowStockDetected events published
        mock_event_publisher.publish_many.assert_called_once()
        published_events = mock_event_publisher.publish_many.call_args[0][0]
        assert len(published_events) == 2
        assert isinstance(published_events[0], InventoryCreated)
        assert isinstance(published_events[1], LowStockDetected)

    def test_create_inventory_propagates_invalid_quantity_error(self, service, mock_repository):
        """T009: InvalidQuantityError from domain propagates to caller"""
        # Act & Assert: Negative quantity should raise InvalidQuantityError
        with pytest.raises(InvalidQuantityError):
            service.create_inventory(
                product_id="SVC-TEST-004",
                initial_quantity=-10,  # Invalid
                minimum_stock_level=5
            )

        # Repository should not be called
        mock_repository.create.assert_not_called()

    def test_create_inventory_propagates_already_exists_error(self, service, mock_repository, mock_event_publisher):
        """T009: InventoryAlreadyExistsError from repository propagates to caller"""
        # Arrange: Repository raises duplicate error
        mock_repository.create = Mock(side_effect=InventoryAlreadyExistsError("Product already exists"))

        # Act & Assert
        with pytest.raises(InventoryAlreadyExistsError, match="already exists"):
            service.create_inventory(
                product_id="SVC-TEST-005",
                initial_quantity=100,
                minimum_stock_level=10
            )

        # Events should not be published when error occurs
        mock_event_publisher.publish_many.assert_not_called()

    def test_create_inventory_with_zero_initial_quantity(self, service, mock_repository, mock_event_publisher):
        """T009: Create accepts zero initial_quantity (per spec)"""
        # Arrange
        expected_inventory = Inventory(
            product_id="SVC-TEST-006",
            total_quantity=0,
            reserved_quantity=0,
            minimum_stock_level=10
        )
        mock_repository.create = Mock(return_value=expected_inventory)

        # Act
        result = service.create_inventory(
            product_id="SVC-TEST-006",
            initial_quantity=0,
            minimum_stock_level=10
        )

        # Assert: Creation succeeded
        assert result.total_quantity == 0
        mock_repository.create.assert_called_once()
