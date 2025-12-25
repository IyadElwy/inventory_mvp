"""
Unit tests for Inventory aggregate.
Tests the domain logic in isolation without external dependencies.
"""
import pytest
from src.domain.inventory import Inventory
from src.domain.exceptions import InvalidQuantityError, InsufficientStockError
from src.domain.events import InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected, InventoryCreated


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


class TestInventoryReserve:
    """Test Inventory.reserve() method"""

    def test_reserve_with_sufficient_stock(self):
        """T036: Reserve inventory with sufficient available stock"""
        inventory = Inventory(
            product_id="PROD-010",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )

        events = inventory.reserve(30)

        assert inventory.reserved_quantity == 50
        assert inventory.available_quantity == 50
        assert len(events) == 1
        assert isinstance(events[0], InventoryReserved)
        assert events[0].product_id == "PROD-010"
        assert events[0].quantity == 30

    def test_reserve_with_insufficient_stock(self):
        """T037: Reserve inventory with insufficient stock raises error"""
        inventory = Inventory(
            product_id="PROD-011",
            total_quantity=100,
            reserved_quantity=90,
            minimum_stock_level=10
        )

        with pytest.raises(InsufficientStockError, match="Cannot reserve 20.*Only 10 available"):
            inventory.reserve(20)

    def test_reserve_emits_inventory_reserved_event(self):
        """T038: Reserve inventory emits InventoryReserved event"""
        inventory = Inventory(
            product_id="PROD-012",
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )

        events = inventory.reserve(25)

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, InventoryReserved)
        assert event.product_id == "PROD-012"
        assert event.quantity == 25
        assert event.timestamp is not None

    def test_reserve_with_negative_quantity_raises_error(self):
        """T039: Reserve with negative quantity raises error"""
        inventory = Inventory(
            product_id="PROD-013",
            total_quantity=100,
            reserved_quantity=0
        )

        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            inventory.reserve(-5)

    def test_reserve_with_zero_quantity_raises_error(self):
        """T039: Reserve with zero quantity raises error"""
        inventory = Inventory(
            product_id="PROD-014",
            total_quantity=100,
            reserved_quantity=0
        )

        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            inventory.reserve(0)


class TestInventoryRelease:
    """Test Inventory.release() method"""

    def test_release_with_valid_quantity(self):
        """T048: Release reserved inventory successfully"""
        inventory = Inventory(
            product_id="PROD-015",
            total_quantity=100,
            reserved_quantity=40,
            minimum_stock_level=10
        )

        events = inventory.release(20)

        assert inventory.reserved_quantity == 20
        assert inventory.available_quantity == 80
        assert len(events) == 1
        assert isinstance(events[0], InventoryReleased)
        assert events[0].product_id == "PROD-015"
        assert events[0].quantity == 20

    def test_release_with_quantity_exceeding_reserved(self):
        """T049: Release quantity exceeding reserved raises error"""
        inventory = Inventory(
            product_id="PROD-016",
            total_quantity=100,
            reserved_quantity=30,
            minimum_stock_level=10
        )

        with pytest.raises(InvalidQuantityError, match="Cannot release 50.*Only 30 reserved"):
            inventory.release(50)

    def test_release_emits_inventory_released_event(self):
        """T050: Release inventory emits InventoryReleased event"""
        inventory = Inventory(
            product_id="PROD-017",
            total_quantity=100,
            reserved_quantity=50,
            minimum_stock_level=10
        )

        events = inventory.release(25)

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, InventoryReleased)
        assert event.product_id == "PROD-017"
        assert event.quantity == 25
        assert event.timestamp is not None

    def test_release_with_negative_quantity_raises_error(self):
        """T049: Release with negative quantity raises error"""
        inventory = Inventory(
            product_id="PROD-018",
            total_quantity=100,
            reserved_quantity=50
        )

        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            inventory.release(-10)

    def test_release_with_zero_quantity_raises_error(self):
        """T049: Release with zero quantity raises error"""
        inventory = Inventory(
            product_id="PROD-019",
            total_quantity=100,
            reserved_quantity=50
        )

        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            inventory.release(0)


class TestInventoryAdjust:
    """Test Inventory.adjust() method"""

    def test_adjust_increasing_total(self):
        """T058: Adjust inventory by increasing total quantity"""
        inventory = Inventory(
            product_id="PROD-020",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )

        events = inventory.adjust(150, "Physical count increase", "manager@example.com")

        assert inventory.total_quantity == 150
        assert inventory.reserved_quantity == 20
        assert inventory.available_quantity == 130
        assert len(events) == 1
        assert isinstance(events[0], InventoryAdjusted)
        assert events[0].product_id == "PROD-020"
        assert events[0].old_quantity == 100
        assert events[0].new_quantity == 150

    def test_adjust_decreasing_total_within_limits(self):
        """T059: Adjust inventory by decreasing total within limits"""
        inventory = Inventory(
            product_id="PROD-021",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )

        events = inventory.adjust(80, "Damaged goods removed", "manager@example.com")

        assert inventory.total_quantity == 80
        assert inventory.reserved_quantity == 20
        assert inventory.available_quantity == 60

    def test_adjust_failing_when_new_total_less_than_reserved(self):
        """T060: Adjust fails when new total is less than reserved"""
        inventory = Inventory(
            product_id="PROD-022",
            total_quantity=100,
            reserved_quantity=50,
            minimum_stock_level=10
        )

        with pytest.raises(InvalidQuantityError, match="New total.*cannot be less than reserved"):
            inventory.adjust(40, "Invalid adjustment", "manager@example.com")

    def test_adjust_emits_inventory_adjusted_event(self):
        """T061: Adjust inventory emits InventoryAdjusted event"""
        inventory = Inventory(
            product_id="PROD-023",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=10
        )

        events = inventory.adjust(120, "Stock recount", "manager@example.com")

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, InventoryAdjusted)
        assert event.product_id == "PROD-023"
        assert event.old_quantity == 100
        assert event.new_quantity == 120
        assert event.timestamp is not None

    def test_adjust_with_negative_total_raises_error(self):
        """T060: Adjust with negative total raises error"""
        inventory = Inventory(
            product_id="PROD-024",
            total_quantity=100,
            reserved_quantity=0
        )

        with pytest.raises(InvalidQuantityError, match="Total quantity cannot be negative"):
            inventory.adjust(-10, "Invalid", "manager@example.com")


class TestLowStockDetection:
    """Test low stock detection in domain methods"""

    def test_reserve_emits_low_stock_when_below_minimum(self):
        """T070: Reserve emits LowStockDetected when available drops below minimum"""
        # Arrange: Create inventory at threshold
        inventory = Inventory(
            product_id="PROD-LOW-010",
            total_quantity=50,
            reserved_quantity=28,
            minimum_stock_level=20
        )

        # Available is currently 22, just above minimum 20
        # Reserve 5 units to drop to 17 (below minimum)

        # Act: Reserve inventory
        events = inventory.reserve(5)

        # Assert: Both InventoryReserved and LowStockDetected events emitted
        assert len(events) == 2
        assert isinstance(events[0], InventoryReserved)
        assert isinstance(events[1], LowStockDetected)
        
        # Verify LowStockDetected event details
        low_stock_event = events[1]
        assert low_stock_event.product_id == "PROD-LOW-010"
        assert low_stock_event.available_quantity == 17
        assert low_stock_event.minimum_stock_level == 20

    def test_reserve_no_low_stock_when_above_minimum(self):
        """Reserve does NOT emit LowStockDetected when still above minimum"""
        # Arrange: Create inventory well above minimum
        inventory = Inventory(
            product_id="PROD-LOW-011",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=30
        )

        # Available is 80, well above minimum 30
        # Reserve 10 units, still at 70 (above minimum)

        # Act: Reserve inventory
        events = inventory.reserve(10)

        # Assert: Only InventoryReserved event, no LowStockDetected
        assert len(events) == 1
        assert isinstance(events[0], InventoryReserved)

    def test_adjust_emits_low_stock_when_below_minimum(self):
        """T071: Adjust emits LowStockDetected when available drops below minimum"""
        # Arrange: Create inventory
        inventory = Inventory(
            product_id="PROD-LOW-012",
            total_quantity=100,
            reserved_quantity=30,
            minimum_stock_level=50
        )

        # Available is currently 70, above minimum 50
        # Adjust down to 60 total, available becomes 30 (below minimum 50)

        # Act: Adjust inventory
        events = inventory.adjust(60, "Damaged goods", "manager@example.com")

        # Assert: Both InventoryAdjusted and LowStockDetected events emitted
        assert len(events) == 2
        assert isinstance(events[0], InventoryAdjusted)
        assert isinstance(events[1], LowStockDetected)
        
        # Verify LowStockDetected event details
        low_stock_event = events[1]
        assert low_stock_event.product_id == "PROD-LOW-012"
        assert low_stock_event.available_quantity == 30
        assert low_stock_event.minimum_stock_level == 50

    def test_adjust_no_low_stock_when_above_minimum(self):
        """Adjust does NOT emit LowStockDetected when still above minimum"""
        # Arrange: Create inventory
        inventory = Inventory(
            product_id="PROD-LOW-013",
            total_quantity=100,
            reserved_quantity=20,
            minimum_stock_level=30
        )

        # Available is 80, well above minimum 30
        # Adjust to 120, available becomes 100 (still above minimum)

        # Act: Adjust inventory
        events = inventory.adjust(120, "Restock", "manager@example.com")

        # Assert: Only InventoryAdjusted event, no LowStockDetected
        assert len(events) == 1
        assert isinstance(events[0], InventoryAdjusted)


class TestInventoryCreateFactory:
    """Test Inventory.create() factory method (T007 - User Story 1)"""

    def test_create_with_valid_inputs(self):
        """T007: Successfully create inventory with valid inputs"""
        # Act: Create inventory using factory method
        inventory, events = Inventory.create(
            product_id="PROD-NEW-001",
            initial_quantity=100,
            minimum_stock_level=10
        )

        # Assert: Inventory entity has correct state
        assert inventory.product_id == "PROD-NEW-001"
        assert inventory.total_quantity == 100
        assert inventory.reserved_quantity == 0
        assert inventory.available_quantity == 100
        assert inventory.minimum_stock_level == 10

        # Assert: InventoryCreated event emitted
        assert len(events) == 1
        assert isinstance(events[0], InventoryCreated)
        assert events[0].product_id == "PROD-NEW-001"
        assert events[0].initial_quantity == 100
        assert events[0].minimum_stock_level == 10
        assert events[0].timestamp is not None

    def test_create_reserved_quantity_is_zero(self):
        """T007: Created inventory always has reserved_quantity=0"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-002",
            initial_quantity=50,
            minimum_stock_level=5
        )

        assert inventory.reserved_quantity == 0
        assert inventory.available_quantity == inventory.total_quantity

    def test_create_emits_inventory_created_event(self):
        """T007: Create emits InventoryCreated event with correct data"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-003",
            initial_quantity=75,
            minimum_stock_level=15
        )

        assert len(events) >= 1
        created_event = events[0]
        assert isinstance(created_event, InventoryCreated)
        assert created_event.product_id == "PROD-NEW-003"
        assert created_event.initial_quantity == 75
        assert created_event.minimum_stock_level == 15

    def test_create_emits_low_stock_when_initial_below_minimum(self):
        """T007: Create emits LowStockDetected when initial_quantity < minimum_stock_level"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-004",
            initial_quantity=5,
            minimum_stock_level=20
        )

        # Assert: Two events emitted
        assert len(events) == 2
        assert isinstance(events[0], InventoryCreated)
        assert isinstance(events[1], LowStockDetected)

        # Verify LowStockDetected event
        low_stock_event = events[1]
        assert low_stock_event.product_id == "PROD-NEW-004"
        assert low_stock_event.available_quantity == 5
        assert low_stock_event.minimum_stock_level == 20

    def test_create_no_low_stock_when_initial_above_minimum(self):
        """T007: Create does NOT emit LowStockDetected when initial >= minimum"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-005",
            initial_quantity=100,
            minimum_stock_level=20
        )

        # Assert: Only InventoryCreated event
        assert len(events) == 1
        assert isinstance(events[0], InventoryCreated)

    def test_create_with_zero_initial_quantity(self):
        """T007: Create accepts zero initial_quantity (valid per spec)"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-006",
            initial_quantity=0,
            minimum_stock_level=10
        )

        assert inventory.total_quantity == 0
        assert inventory.available_quantity == 0
        assert len(events) == 2  # InventoryCreated + LowStockDetected

    def test_create_with_zero_minimum_stock_level(self):
        """T007: Create accepts zero minimum_stock_level (valid per spec)"""
        inventory, events = Inventory.create(
            product_id="PROD-NEW-007",
            initial_quantity=50,
            minimum_stock_level=0
        )

        assert inventory.minimum_stock_level == 0
        assert len(events) == 1  # Only InventoryCreated

    def test_create_with_negative_initial_quantity_raises_error(self):
        """T007: Create with negative initial_quantity raises InvalidQuantityError"""
        with pytest.raises(InvalidQuantityError, match="Initial quantity.*must be non-negative"):
            Inventory.create(
                product_id="PROD-NEW-008",
                initial_quantity=-10,
                minimum_stock_level=5
            )

    def test_create_with_negative_minimum_stock_raises_error(self):
        """T007: Create with negative minimum_stock_level raises InvalidQuantityError"""
        with pytest.raises(InvalidQuantityError, match="Minimum stock level.*must be non-negative"):
            Inventory.create(
                product_id="PROD-NEW-009",
                initial_quantity=100,
                minimum_stock_level=-5
            )

    def test_create_with_empty_product_id_raises_error(self):
        """T007: Create with empty product_id raises InvalidQuantityError"""
        with pytest.raises(InvalidQuantityError, match="Product ID.*cannot be empty"):
            Inventory.create(
                product_id="",
                initial_quantity=100,
                minimum_stock_level=10
            )

    def test_create_with_whitespace_product_id_raises_error(self):
        """T007: Create with whitespace-only product_id raises InvalidQuantityError"""
        with pytest.raises(InvalidQuantityError, match="Product ID.*cannot be empty"):
            Inventory.create(
                product_id="   ",
                initial_quantity=100,
                minimum_stock_level=10
            )

    # T018: Additional comprehensive validation tests for User Story 2

    def test_create_with_special_characters_in_product_id(self):
        """T018: Create accepts product_id with special characters (per spec)"""
        inventory, events = Inventory.create(
            product_id="PROD-123!@#$%",
            initial_quantity=50,
            minimum_stock_level=5
        )

        assert inventory.product_id == "PROD-123!@#$%"
        assert len(events) >= 1

    def test_create_with_unicode_product_id(self):
        """T018: Create accepts product_id with Unicode characters (per spec)"""
        inventory, events = Inventory.create(
            product_id="产品-001-™",
            initial_quantity=25,
            minimum_stock_level=2
        )

        assert inventory.product_id == "产品-001-™"
        assert len(events) >= 1

    def test_create_error_messages_are_clear_and_actionable(self):
        """T018: Error messages clearly explain the validation failure"""
        # Test negative initial_quantity
        try:
            Inventory.create("PROD-001", -5, 10)
            assert False, "Should have raised InvalidQuantityError"
        except InvalidQuantityError as e:
            assert "non-negative" in str(e).lower()

        # Test negative minimum_stock_level
        try:
            Inventory.create("PROD-002", 100, -10)
            assert False, "Should have raised InvalidQuantityError"
        except InvalidQuantityError as e:
            assert "non-negative" in str(e).lower()

        # Test empty product_id
        try:
            Inventory.create("", 100, 10)
            assert False, "Should have raised InvalidQuantityError"
        except InvalidQuantityError as e:
            assert "empty" in str(e).lower()

    def test_create_with_zero_both_quantities(self):
        """T018: Create accepts zero for both initial_quantity and minimum_stock_level"""
        inventory, events = Inventory.create(
            product_id="PROD-ZERO",
            initial_quantity=0,
            minimum_stock_level=0
        )

        assert inventory.total_quantity == 0
        assert inventory.minimum_stock_level == 0
        # Should only emit InventoryCreated, not LowStockDetected (0 is not < 0)
        assert len(events) == 1
        assert isinstance(events[0], InventoryCreated)

    def test_create_minimum_above_initial_is_allowed(self):
        """T018: Creating inventory with minimum > initial is valid (triggers low stock)"""
        inventory, events = Inventory.create(
            product_id="PROD-LOW-START",
            initial_quantity=10,
            minimum_stock_level=50
        )

        assert inventory.total_quantity == 10
        assert inventory.minimum_stock_level == 50
        # Should emit both events
        assert len(events) == 2
        assert isinstance(events[0], InventoryCreated)
        assert isinstance(events[1], LowStockDetected)
