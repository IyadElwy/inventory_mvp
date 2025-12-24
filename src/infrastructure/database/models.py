"""
SQLAlchemy models for inventory persistence.
Maps domain aggregates to database tables.
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class InventoryModel(Base):
    """
    SQLAlchemy model for inventory persistence.
    Maps to 'inventory' table.
    """
    __tablename__ = 'inventory'

    product_id = Column(String, primary_key=True, index=True)
    total_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    minimum_stock_level = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_domain(self):
        """Convert SQLAlchemy model to domain aggregate"""
        from src.domain.inventory import Inventory
        return Inventory(
            product_id=self.product_id,
            total_quantity=self.total_quantity,
            reserved_quantity=self.reserved_quantity,
            minimum_stock_level=self.minimum_stock_level
        )

    @staticmethod
    def from_domain(inventory):
        """Convert domain aggregate to SQLAlchemy model"""
        return InventoryModel(
            product_id=inventory.product_id,
            total_quantity=inventory.total_quantity,
            reserved_quantity=inventory.reserved_quantity,
            minimum_stock_level=inventory.minimum_stock_level
        )


class EventLogModel(Base):
    """
    SQLAlchemy model for event log persistence.
    Maps to 'event_log' table for audit trail.
    """
    __tablename__ = 'event_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=False, index=True)
    event_data = Column(String, nullable=False)  # JSON-serialized event
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
