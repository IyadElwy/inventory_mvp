"""
Pytest configuration and fixtures for all tests.
Sets up test database and common fixtures.
"""
import pytest
from src.infrastructure.database.models import Base
from src.infrastructure.database.session import engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create database tables before all tests and drop them after.
    This runs once per test session.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_tables():
    """
    Clean up database tables between individual tests.
    This runs before each test.
    """
    yield

    # After each test, delete all data but keep tables
    with engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()
