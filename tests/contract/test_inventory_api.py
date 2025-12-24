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
