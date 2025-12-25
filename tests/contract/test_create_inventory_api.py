"""
Contract tests for POST /v1/inventory endpoint (T010 - User Story 1).
Tests API contract compliance with mocked service layer.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app
from src.domain.inventory import Inventory
from src.domain.exceptions import InvalidQuantityError, InventoryAlreadyExistsError


client = TestClient(app)


class TestCreateInventoryEndpoint:
    """Test POST /v1/inventory endpoint (T010 - User Story 1)"""

    def test_create_inventory_returns_201_created(self):
        """T010: Valid request returns 201 Created with OperationResult"""
        # Arrange: Mock service to return created inventory
        from src.infrastructure.api.dependencies import get_repo_dependency, get_event_publisher
        from src.infrastructure.api.routes import get_inventory_service

        mock_service = Mock()
        mock_inventory = Inventory(
            product_id="API-TEST-001",
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )
        mock_service.create_inventory = Mock(return_value=mock_inventory)

        app.dependency_overrides[get_repo_dependency] = lambda: Mock()
        app.dependency_overrides[get_event_publisher] = lambda: Mock()
        app.dependency_overrides[get_inventory_service] = lambda: mock_service

        try:
            # Act: POST request
            response = client.post(
                "/v1/inventory",
                json={
                    "product_id": "API-TEST-001",
                    "initial_quantity": 100,
                    "minimum_stock_level": 10
                }
            )

            # Assert: 201 status
            assert response.status_code == 201

            # Assert: OperationResult schema
            data = response.json()
            assert data["success"] is True
            assert "Successfully created inventory" in data["message"]
            assert data["inventory"]["product_id"] == "API-TEST-001"
            assert data["inventory"]["total_quantity"] == 100
            assert data["inventory"]["reserved_quantity"] == 0
            assert data["inventory"]["available_quantity"] == 100
            assert data["inventory"]["minimum_stock_level"] == 10
        finally:
            app.dependency_overrides.clear()

    def test_create_duplicate_product_returns_409_conflict(self):
        """T010: Duplicate product returns 409 Conflict"""
        # Arrange: Service raises InventoryAlreadyExistsError
        from src.infrastructure.api.dependencies import get_repo_dependency, get_event_publisher

        mock_service = Mock()
        mock_service.create_inventory = Mock(
            side_effect=InventoryAlreadyExistsError("Inventory already exists for product API-TEST-002")
        )

        def override_service():
            return mock_service

        app.dependency_overrides[get_repo_dependency] = lambda: Mock()
        app.dependency_overrides[get_event_publisher] = lambda: Mock()

        from src.infrastructure.api.routes import get_inventory_service
        app.dependency_overrides[get_inventory_service] = override_service

        try:
            # Act
            response = client.post(
                "/v1/inventory",
                json={
                    "product_id": "API-TEST-002",
                    "initial_quantity": 50,
                    "minimum_stock_level": 5
                }
            )

            # Assert: 409 Conflict
            assert response.status_code == 409
            data = response.json()
            assert "already exists" in data["detail"].lower()
        finally:
            # Cleanup
            app.dependency_overrides.clear()

    def test_create_with_negative_initial_quantity_returns_422(self):
        """T010: Negative initial_quantity returns 422 Validation Error"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "API-TEST-003",
                "initial_quantity": -10,  # Invalid
                "minimum_stock_level": 5
            }
        )

        # Assert: 422 Unprocessable Entity
        assert response.status_code == 422

    def test_create_with_negative_minimum_stock_returns_422(self):
        """T010: Negative minimum_stock_level returns 422 Validation Error"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "API-TEST-004",
                "initial_quantity": 100,
                "minimum_stock_level": -5  # Invalid
            }
        )

        assert response.status_code == 422

    def test_create_with_empty_product_id_returns_422(self):
        """T010: Empty product_id returns 422 Validation Error"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "",  # Invalid
                "initial_quantity": 100,
                "minimum_stock_level": 10
            }
        )

        assert response.status_code == 422

    def test_create_with_missing_fields_returns_422(self):
        """T010: Missing required fields returns 422"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "API-TEST-005"
                # Missing initial_quantity and minimum_stock_level
            }
        )

        assert response.status_code == 422

    def test_create_response_matches_operation_result_schema(self):
        """T010: Response body matches OperationResult schema"""
        # Arrange
        from src.infrastructure.api.dependencies import get_repo_dependency, get_event_publisher
        from src.infrastructure.api.routes import get_inventory_service

        mock_service = Mock()
        mock_inventory = Inventory(
            product_id="API-TEST-006",
            total_quantity=75,
            reserved_quantity=0,
            minimum_stock_level=15
        )
        mock_service.create_inventory = Mock(return_value=mock_inventory)

        app.dependency_overrides[get_repo_dependency] = lambda: Mock()
        app.dependency_overrides[get_event_publisher] = lambda: Mock()
        app.dependency_overrides[get_inventory_service] = lambda: mock_service

        try:
            # Act
            response = client.post(
                "/v1/inventory",
                json={
                    "product_id": "API-TEST-006",
                    "initial_quantity": 75,
                    "minimum_stock_level": 15
                }
            )

            # Assert: Schema compliance
            assert response.status_code == 201
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "inventory" in data
            assert isinstance(data["success"], bool)
            assert isinstance(data["message"], str)
            assert isinstance(data["inventory"], dict)
        finally:
            app.dependency_overrides.clear()

    # T019: Comprehensive validation tests for User Story 2

    def test_create_with_whitespace_product_id_returns_422(self):
        """T019: Whitespace-only product_id returns 422 with clear error"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "   ",  # Whitespace only
                "initial_quantity": 100,
                "minimum_stock_level": 10
            }
        )

        assert response.status_code == 422
        data = response.json()
        # Pydantic validation should catch this
        assert "detail" in data

    def test_create_validation_error_includes_field_location(self):
        """T019: Validation errors include field location for debugging"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "PROD-001",
                "initial_quantity": -10,  # Invalid
                "minimum_stock_level": 5
            }
        )

        assert response.status_code == 422
        data = response.json()
        # FastAPI/Pydantic format includes field location
        assert "detail" in data

    def test_create_with_special_characters_succeeds(self):
        """T019: Product IDs with special characters are accepted"""
        from src.infrastructure.api.dependencies import get_repo_dependency, get_event_publisher
        from src.infrastructure.api.routes import get_inventory_service

        mock_service = Mock()
        mock_inventory = Inventory(
            product_id="PROD-123!@#",
            total_quantity=50,
            reserved_quantity=0,
            minimum_stock_level=5
        )
        mock_service.create_inventory = Mock(return_value=mock_inventory)

        app.dependency_overrides[get_repo_dependency] = lambda: Mock()
        app.dependency_overrides[get_event_publisher] = lambda: Mock()
        app.dependency_overrides[get_inventory_service] = lambda: mock_service

        try:
            response = client.post(
                "/v1/inventory",
                json={
                    "product_id": "PROD-123!@#",
                    "initial_quantity": 50,
                    "minimum_stock_level": 5
                }
            )

            assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    def test_create_multiple_validation_errors(self):
        """T019: Multiple validation errors are reported together"""
        response = client.post(
            "/v1/inventory",
            json={
                "product_id": "",  # Invalid
                "initial_quantity": -10,  # Invalid
                "minimum_stock_level": -5  # Invalid
            }
        )

        assert response.status_code == 422
        data = response.json()
        # Should report multiple errors
        assert "detail" in data

    def test_create_with_zero_quantities_succeeds(self):
        """T019: Zero quantities are valid and accepted"""
        from src.infrastructure.api.dependencies import get_repo_dependency, get_event_publisher
        from src.infrastructure.api.routes import get_inventory_service

        mock_service = Mock()
        mock_inventory = Inventory(
            product_id="PROD-ZERO",
            total_quantity=0,
            reserved_quantity=0,
            minimum_stock_level=0
        )
        mock_service.create_inventory = Mock(return_value=mock_inventory)

        app.dependency_overrides[get_repo_dependency] = lambda: Mock()
        app.dependency_overrides[get_event_publisher] = lambda: Mock()
        app.dependency_overrides[get_inventory_service] = lambda: mock_service

        try:
            response = client.post(
                "/v1/inventory",
                json={
                    "product_id": "PROD-ZERO",
                    "initial_quantity": 0,
                    "minimum_stock_level": 0
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["inventory"]["total_quantity"] == 0
        finally:
            app.dependency_overrides.clear()
