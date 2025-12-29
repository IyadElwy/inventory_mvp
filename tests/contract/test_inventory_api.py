"""
Contract tests for Inventory API endpoints.
Tests the API contract (request/response schemas) using FastAPI TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.database.repository import InventoryRepository
from src.infrastructure.database.session import get_db
from src.domain.inventory import Inventory


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session"""
    session = next(get_db())
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def setup_test_inventory(db_session):
    """Setup test inventory in database"""
    repository = InventoryRepository(db_session)

    # Create test inventory
    inventory = Inventory(
        product_id="PROD-API-001",
        total_quantity=150,
        reserved_quantity=30,
        minimum_stock_level=15
    )
    repository.save(inventory)

    return inventory


class TestGetInventoryEndpoint:
    """T030: Test GET /v1/inventory/{product_id} endpoint contract"""

    def test_get_inventory_success(self, client, setup_test_inventory):
        """GET inventory returns correct schema with 200"""
        # Act: Call API endpoint
        response = client.get("/v1/inventory/PROD-API-001")

        # Assert: Status code and response schema
        assert response.status_code == 200

        data = response.json()
        assert "product_id" in data
        assert "total_quantity" in data
        assert "reserved_quantity" in data
        assert "available_quantity" in data
        assert "minimum_stock_level" in data

        # Assert: Correct values
        assert data["product_id"] == "PROD-API-001"
        assert data["total_quantity"] == 150
        assert data["reserved_quantity"] == 30
        assert data["available_quantity"] == 120
        assert data["minimum_stock_level"] == 15

    def test_get_inventory_not_found(self, client):
        """GET inventory for non-existent product returns 404"""
        # Act: Call API with non-existent product
        response = client.get("/v1/inventory/PROD-NONEXISTENT")

        # Assert: 404 status code
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "PROD-NONEXISTENT" in data["detail"]

    def test_get_inventory_response_schema(self, client, setup_test_inventory):
        """GET inventory returns correct Pydantic schema"""
        # Act: Call API endpoint
        response = client.get("/v1/inventory/PROD-API-001")

        # Assert: Response matches InventoryResponse schema
        assert response.status_code == 200

        data = response.json()

        # Schema validation: all fields present and correct types
        assert isinstance(data["product_id"], str)
        assert isinstance(data["total_quantity"], int)
        assert isinstance(data["reserved_quantity"], int)
        assert isinstance(data["available_quantity"], int)
        assert isinstance(data["minimum_stock_level"], int)

        # Schema validation: no extra fields
        expected_fields = {
            "product_id", "total_quantity", "reserved_quantity",
            "available_quantity", "minimum_stock_level"
        }
        assert set(data.keys()) == expected_fields


class TestReserveInventoryEndpoint:
    """T041: Test POST /v1/inventory/{product_id}/reserve endpoint contract"""

    def test_reserve_inventory_success(self, client, setup_test_inventory, db_session):
        """POST reserve inventory returns correct schema with 200"""
        # Arrange: Setup request payload
        request_data = {
            "quantity": 20,
            "order_id": "ORDER-TEST-001"
        }

        # Act: Call API endpoint
        response = client.post("/v1/inventory/PROD-API-001/reserve", json=request_data)

        # Assert: Status code and response schema
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "inventory" in data

        assert data["success"] is True

        # Verify inventory state
        inventory = data["inventory"]
        assert inventory["product_id"] == "PROD-API-001"
        assert inventory["reserved_quantity"] == 50  # 30 + 20
        assert inventory["available_quantity"] == 100  # 150 - 20

    def test_reserve_inventory_insufficient_stock(self, client, setup_test_inventory):
        """POST reserve with insufficient stock returns 409"""
        # Arrange: Try to reserve more than available
        request_data = {
            "quantity": 200,
            "order_id": "ORDER-TEST-002"
        }

        # Act: Call API endpoint
        response = client.post("/v1/inventory/PROD-API-001/reserve", json=request_data)

        # Assert: 409 Conflict status code
        assert response.status_code == 409

        data = response.json()
        assert "detail" in data
        assert "Cannot reserve" in data["detail"]

    def test_reserve_inventory_product_not_found(self, client):
        """POST reserve for non-existent product returns 404"""
        # Arrange: Valid request for non-existent product
        request_data = {
            "quantity": 10,
            "order_id": "ORDER-TEST-003"
        }

        # Act: Call API with non-existent product
        response = client.post("/v1/inventory/PROD-NONEXISTENT/reserve", json=request_data)

        # Assert: 404 status code
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "PROD-NONEXISTENT" in data["detail"]

    def test_reserve_inventory_invalid_quantity(self, client, setup_test_inventory):
        """POST reserve with invalid quantity returns 422"""
        # Arrange: Negative quantity
        request_data = {
            "quantity": -10,
            "order_id": "ORDER-TEST-004"
        }

        # Act: Call API endpoint
        response = client.post("/v1/inventory/PROD-API-001/reserve", json=request_data)

        # Assert: 422 Validation Error
        assert response.status_code == 422


class TestReleaseInventoryEndpoint:
    """T052: Test POST /v1/inventory/{product_id}/release endpoint contract"""

    def test_release_inventory_success(self, client, setup_test_inventory, db_session):
        """POST release inventory returns correct schema with 200"""
        # Arrange: First reserve some inventory, then release it
        reserve_request = {
            "quantity": 40,
            "order_id": "ORDER-RELEASE-001"
        }
        client.post("/v1/inventory/PROD-API-001/reserve", json=reserve_request)

        # Prepare release request
        release_request = {
            "quantity": 20,
            "order_id": "ORDER-RELEASE-001",
            "reason": "Customer cancellation"
        }

        # Act: Call release API endpoint
        response = client.post("/v1/inventory/PROD-API-001/release", json=release_request)

        # Assert: Status code and response schema
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "inventory" in data

        assert data["success"] is True

        # Verify inventory state (started with 30 reserved, added 40, released 20 = 50 reserved)
        inventory = data["inventory"]
        assert inventory["product_id"] == "PROD-API-001"
        assert inventory["reserved_quantity"] == 50  # 30 + 40 - 20

    def test_release_inventory_exceeding_reserved(self, client, setup_test_inventory):
        """POST release exceeding reserved quantity returns 422"""
        # Arrange: Try to release more than reserved
        release_request = {
            "quantity": 200,
            "order_id": "ORDER-RELEASE-002",
            "reason": "Test error"
        }

        # Act: Call API endpoint
        response = client.post("/v1/inventory/PROD-API-001/release", json=release_request)

        # Assert: 422 Validation Error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert "Cannot release" in data["detail"]

    def test_release_inventory_product_not_found(self, client):
        """POST release for non-existent product returns 404"""
        # Arrange: Valid request for non-existent product
        release_request = {
            "quantity": 10,
            "order_id": "ORDER-RELEASE-003",
            "reason": "Test"
        }

        # Act: Call API with non-existent product
        response = client.post("/v1/inventory/PROD-NONEXISTENT/release", json=release_request)

        # Assert: 404 status code
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "PROD-NONEXISTENT" in data["detail"]

    def test_release_inventory_invalid_quantity(self, client, setup_test_inventory):
        """POST release with invalid quantity returns 422"""
        # Arrange: Negative quantity
        release_request = {
            "quantity": -10,
            "order_id": "ORDER-RELEASE-004",
            "reason": "Test"
        }

        # Act: Call API endpoint
        response = client.post("/v1/inventory/PROD-API-001/release", json=release_request)

        # Assert: 422 Validation Error
        assert response.status_code == 422


class TestAdjustInventoryEndpoint:
    """T063: Test PUT /v1/inventory/{product_id} endpoint contract"""

    def test_adjust_inventory_success(self, client, setup_test_inventory, db_session):
        """PUT adjust inventory returns correct schema with 200"""
        # Arrange: Prepare adjustment request
        adjust_request = {
            "new_quantity": 200,
            "reason": "Physical stock count",
            "adjusted_by": "manager@example.com"
        }

        # Act: Call API endpoint
        response = client.put("/v1/inventory/PROD-API-001", json=adjust_request)

        # Assert: Status code and response schema
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "inventory" in data

        assert data["success"] is True

        # Verify inventory state
        inventory = data["inventory"]
        assert inventory["product_id"] == "PROD-API-001"
        assert inventory["total_quantity"] == 200

    def test_adjust_inventory_below_reserved_fails(self, client, setup_test_inventory):
        """PUT adjust below reserved quantity returns 422"""
        # Arrange: First reserve some inventory
        reserve_request = {"quantity": 100, "order_id": "ORDER-ADJ-001"}
        client.post("/v1/inventory/PROD-API-001/reserve", json=reserve_request)

        # Try to adjust below reserved
        adjust_request = {
            "new_quantity": 50,  # Less than 130 reserved (30 + 100)
            "reason": "Invalid adjustment",
            "adjusted_by": "manager@example.com"
        }

        # Act: Call API endpoint
        response = client.put("/v1/inventory/PROD-API-001", json=adjust_request)

        # Assert: 422 Validation Error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert "cannot be less than reserved" in data["detail"]

    def test_adjust_inventory_product_not_found(self, client):
        """PUT adjust for non-existent product returns 404"""
        # Arrange: Valid request for non-existent product
        adjust_request = {
            "new_quantity": 100,
            "reason": "Test",
            "adjusted_by": "manager@example.com"
        }

        # Act: Call API with non-existent product
        response = client.put("/v1/inventory/PROD-NONEXISTENT", json=adjust_request)

        # Assert: 404 status code
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "PROD-NONEXISTENT" in data["detail"]

    def test_adjust_inventory_negative_quantity(self, client, setup_test_inventory):
        """PUT adjust with negative quantity returns 422"""
        # Arrange: Negative new quantity
        adjust_request = {
            "new_quantity": -10,
            "reason": "Invalid",
            "adjusted_by": "manager@example.com"
        }

        # Act: Call API endpoint
        response = client.put("/v1/inventory/PROD-API-001", json=adjust_request)

        # Assert: 422 Validation Error for negative quantity
        assert response.status_code == 422


class TestLowStockEndpoint:
    """T073: Test GET /v1/inventory/low-stock endpoint contract"""

    def test_get_low_stock_items(self, client, db_session):
        """GET low-stock returns products below minimum threshold"""
        # Arrange: Create multiple products, some below minimum
        repository = InventoryRepository(db_session)

        # Product 1: Below minimum (available=10, minimum=20)
        inventory1 = Inventory(
            product_id="PROD-LS-001",
            total_quantity=30,
            reserved_quantity=20,
            minimum_stock_level=20
        )
        repository.save(inventory1)

        # Product 2: Below minimum (available=5, minimum=15)
        inventory2 = Inventory(
            product_id="PROD-LS-002",
            total_quantity=25,
            reserved_quantity=20,
            minimum_stock_level=15
        )
        repository.save(inventory2)

        # Product 3: Above minimum (available=100, minimum=20)
        inventory3 = Inventory(
            product_id="PROD-LS-003",
            total_quantity=120,
            reserved_quantity=20,
            minimum_stock_level=20
        )
        repository.save(inventory3)

        # Act: Call low-stock API endpoint
        response = client.get("/v1/inventory/low-stock")

        # Assert: Status code and response schema
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Assert: At least our low-stock products are returned
        product_ids = [item["product_id"] for item in data]
        assert "PROD-LS-001" in product_ids
        assert "PROD-LS-002" in product_ids
        assert "PROD-LS-003" not in product_ids  # This one is above minimum

        # Assert: Response schema for each item
        for item in data:
            assert "product_id" in item
            assert "total_quantity" in item
            assert "reserved_quantity" in item
            assert "available_quantity" in item
            assert "minimum_stock_level" in item

            # Verify each item is indeed below minimum
            assert item["available_quantity"] < item["minimum_stock_level"]

    def test_get_low_stock_empty_when_all_above_minimum(self, client, db_session):
        """GET low-stock returns empty list when all products above minimum"""
        # Arrange: Create products all above minimum
        repository = InventoryRepository(db_session)

        inventory = Inventory(
            product_id="PROD-LS-100",
            total_quantity=200,
            reserved_quantity=50,
            minimum_stock_level=100
        )
        repository.save(inventory)

        # Act: Call low-stock API endpoint
        response = client.get("/v1/inventory/low-stock")

        # Assert: Response OK and this specific product is NOT in low stock
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Our product should NOT be in the results (it's above minimum)
        product_ids = [item["product_id"] for item in data]
        assert "PROD-LS-100" not in product_ids

    def test_get_low_stock_response_schema(self, client, db_session):
        """GET low-stock returns correct Pydantic schema"""
        # Arrange: Create one low-stock product
        repository = InventoryRepository(db_session)

        inventory = Inventory(
            product_id="PROD-LS-200",
            total_quantity=15,
            reserved_quantity=10,
            minimum_stock_level=10
        )
        repository.save(inventory)

        # Act: Call API endpoint
        response = client.get("/v1/inventory/low-stock")

        # Assert: Response matches expected schema
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least our product should be there

        # Find our specific product in the results
        our_product = next((item for item in data if item["product_id"] == "PROD-LS-200"), None)
        assert our_product is not None, "PROD-LS-200 should be in low stock results"

        item = our_product

        # Schema validation: all fields present and correct types
        assert isinstance(item["product_id"], str)
        assert isinstance(item["total_quantity"], int)
        assert isinstance(item["reserved_quantity"], int)
        assert isinstance(item["available_quantity"], int)
        assert isinstance(item["minimum_stock_level"], int)

        # Schema validation: expected field set
        expected_fields = {
            "product_id", "total_quantity", "reserved_quantity",
            "available_quantity", "minimum_stock_level"
        }
        assert set(item.keys()) == expected_fields
