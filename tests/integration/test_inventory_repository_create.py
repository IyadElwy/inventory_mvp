"""
Integration tests for Repository.create() method (T008 - User Story 1).
Tests database persistence with actual database integration.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from src.domain.inventory import Inventory
from src.domain.exceptions import InventoryAlreadyExistsError
from src.infrastructure.database.models import Base, InventoryModel
from src.infrastructure.database.repository import InventoryRepository


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """Create repository with test database session"""
    return InventoryRepository(db_session)


class TestRepositoryCreate:
    """Test Repository.create() method (T008 - User Story 1)"""

    def test_create_persists_new_inventory(self, repository, db_session):
        """T008: Successfully persist new inventory to database"""
        # Arrange: Create inventory entity
        inventory = Inventory(
            product_id="REPO-TEST-001",
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )

        # Act: Persist via repository
        created = repository.create(inventory)

        # Assert: Entity was persisted and returned
        assert created.product_id == "REPO-TEST-001"
        assert created.total_quantity == 100
        assert created.reserved_quantity == 0
        assert created.minimum_stock_level == 10

        # Verify in database
        db_model = db_session.query(InventoryModel).filter_by(product_id="REPO-TEST-001").first()
        assert db_model is not None
        assert db_model.product_id == "REPO-TEST-001"
        assert db_model.total_quantity == 100

    def test_create_duplicate_product_raises_error(self, repository):
        """T008: Creating inventory for existing product raises InventoryAlreadyExistsError"""
        # Arrange: Create first inventory
        inventory1 = Inventory(
            product_id="REPO-TEST-002",
            total_quantity=50,
            reserved_quantity=0,
            minimum_stock_level=5
        )
        repository.create(inventory1)

        # Act & Assert: Attempt to create duplicate
        inventory2 = Inventory(
            product_id="REPO-TEST-002",  # Same product_id
            total_quantity=100,
            reserved_quantity=0,
            minimum_stock_level=10
        )

        with pytest.raises(InventoryAlreadyExistsError, match="already exists.*REPO-TEST-002"):
            repository.create(inventory2)

    def test_create_returns_entity_with_all_fields(self, repository):
        """T008: Created entity includes all fields including database-generated ones"""
        # Arrange
        inventory = Inventory(
            product_id="REPO-TEST-003",
            total_quantity=75,
            reserved_quantity=0,
            minimum_stock_level=15
        )

        # Act
        created = repository.create(inventory)

        # Assert: All fields present
        assert created.product_id == "REPO-TEST-003"
        assert created.total_quantity == 75
        assert created.reserved_quantity == 0
        assert created.minimum_stock_level == 15
        assert created.available_quantity == 75  # Computed property

    def test_create_with_zero_quantities(self, repository):
        """T008: Create accepts zero quantities (per spec)"""
        inventory = Inventory(
            product_id="REPO-TEST-004",
            total_quantity=0,
            reserved_quantity=0,
            minimum_stock_level=0
        )

        created = repository.create(inventory)

        assert created.total_quantity == 0
        assert created.minimum_stock_level == 0
