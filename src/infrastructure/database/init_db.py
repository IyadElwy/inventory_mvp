"""
Database initialization script.
Creates all tables using SQLAlchemy metadata.
"""
import os
from pathlib import Path
from src.infrastructure.database.models import Base
from src.infrastructure.database.session import engine


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    # Ensure data directory exists
    db_path = os.getenv('DATABASE_PATH', './data/inventory.db')
    data_dir = Path(db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    # Can be run standalone for manual DB initialization
    init_db()
