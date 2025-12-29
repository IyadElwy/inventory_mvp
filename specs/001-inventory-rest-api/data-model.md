# Data Model: Inventory Management REST API

**Feature**: 001-inventory-rest-api
**Date**: 2025-12-24
**Phase**: Phase 1 - Data Model Design

## Overview

This document defines the data model for the Inventory Management microservice across three architectural layers:
1. **Domain Layer**: Business entities and value objects (pure Python dataclasses)
2. **Infrastructure Layer**: Persistence models (SQLAlchemy ORM)
3. **API Layer**: Request/response schemas (Pydantic models)

## Domain Model (Business Logic)

### Inventory Aggregate

**File**: `src/domain/inventory.py`

```python
from dataclasses import dataclass
from typing import List
from .events import InventoryEvent
from .exceptions import InsufficientStockError, InvalidQuantityError

@dataclass
class Inventory:
    """
    Aggregate Root for inventory management.
    Enforces business invariants and emits domain events.
    """
    product_id: str
    total_quantity: int
    reserved_quantity: int
    minimum_stock_level: int

    @property
    def available_quantity(self) -> int:
        """Calculated field: TotalQuantity - ReservedQuantity"""
        return self.total_quantity - self.reserved_quantity

    def __post_init__(self):
        """Validate invariants on creation"""
        self._validate_invariants()

    def _validate_invariants(self):
        """Enforce business rules"""
        if self.total_quantity < 0:
            raise InvalidQuantityError("Total quantity cannot be negative")
        if self.reserved_quantity < 0:
            raise InvalidQuantityError("Reserved quantity cannot be negative")
        if self.reserved_quantity > self.total_quantity:
            raise InvalidQuantityError("Reserved quantity cannot exceed total quantity")
        if self.minimum_stock_level < 0:
            raise InvalidQuantityError("Minimum stock level cannot be negative")

    def reserve(self, quantity: int) -> List[InventoryEvent]:
        """
        Reserve inventory for an order.
        Returns: List of events (InventoryReserved, optionally LowStockDetected)
        Raises: InsufficientStockError if quantity > available_quantity
        """
        if quantity <= 0:
            raise InvalidQuantityError("Reservation quantity must be positive")

        if quantity > self.available_quantity:
            raise InsufficientStockError(
                f"Cannot reserve {quantity} units. Only {self.available_quantity} available."
            )

        self.reserved_quantity += quantity
        self._validate_invariants()

        from .events import InventoryReserved, LowStockDetected
        events = [InventoryReserved(product_id=self.product_id, quantity=quantity)]

        # Check low stock condition
        if self.available_quantity < self.minimum_stock_level:
            events.append(LowStockDetected(
                product_id=self.product_id,
                available_quantity=self.available_quantity,
                minimum_stock_level=self.minimum_stock_level
            ))

        return events

    def release(self, quantity: int) -> List[InventoryEvent]:
        """
        Release previously reserved inventory.
        Returns: List of events (InventoryReleased)
        Raises: InvalidQuantityError if quantity > reserved_quantity
        """
        if quantity <= 0:
            raise InvalidQuantityError("Release quantity must be positive")

        if quantity > self.reserved_quantity:
            raise InvalidQuantityError(
                f"Cannot release {quantity} units. Only {self.reserved_quantity} reserved."
            )

        self.reserved_quantity -= quantity
        self._validate_invariants()

        from .events import InventoryReleased
        return [InventoryReleased(product_id=self.product_id, quantity=quantity)]

    def adjust(self, new_total_quantity: int) -> List[InventoryEvent]:
        """
        Manually adjust total inventory quantity.
        Returns: List of events (InventoryAdjusted, optionally LowStockDetected)
        Raises: InvalidQuantityError if adjustment violates invariants
        """
        if new_total_quantity < 0:
            raise InvalidQuantityError("Total quantity cannot be negative")

        if new_total_quantity < self.reserved_quantity:
            raise InvalidQuantityError(
                f"Cannot adjust to {new_total_quantity}. "
                f"{self.reserved_quantity} units currently reserved."
            )

        old_quantity = self.total_quantity
        self.total_quantity = new_total_quantity
        self._validate_invariants()

        from .events import InventoryAdjusted, LowStockDetected
        events = [InventoryAdjusted(
            product_id=self.product_id,
            old_quantity=old_quantity,
            new_quantity=new_total_quantity
        )]

        # Check low stock condition
        if self.available_quantity < self.minimum_stock_level:
            events.append(LowStockDetected(
                product_id=self.product_id,
                available_quantity=self.available_quantity,
                minimum_stock_level=self.minimum_stock_level
            ))

        return events
```

### Domain Commands

**File**: `src/domain/commands.py`

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ReserveInventory:
    """Command to reserve inventory for an order"""
    product_id: str
    quantity: int
    order_id: str  # For idempotency tracking
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class ReleaseInventory:
    """Command to release reserved inventory"""
    product_id: str
    quantity: int
    order_id: str
    reason: str  # e.g., "order_cancelled", "payment_failed"
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class AdjustInventory:
    """Command to manually adjust inventory"""
    product_id: str
    new_quantity: int
    reason: str  # e.g., "physical_count", "damaged_goods"
    adjusted_by: str  # User or system ID
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### Domain Events

**File**: `src/domain/events.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

class InventoryEvent(Protocol):
    """Base protocol for all inventory events"""
    product_id: str
    timestamp: datetime

@dataclass(frozen=True)
class InventoryReserved:
    """Event: Inventory successfully reserved"""
    product_id: str
    quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class InventoryReleased:
    """Event: Reserved inventory released back to available"""
    product_id: str
    quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class InventoryAdjusted:
    """Event: Inventory manually adjusted"""
    product_id: str
    old_quantity: int
    new_quantity: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class LowStockDetected:
    """Event: Inventory fell below minimum threshold"""
    product_id: str
    available_quantity: int
    minimum_stock_level: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### Domain Exceptions

**File**: `src/domain/exceptions.py`

```python
class InventoryDomainError(Exception):
    """Base exception for inventory domain errors"""
    pass

class InvalidQuantityError(InventoryDomainError):
    """Raised when quantity violates business rules"""
    pass

class InsufficientStockError(InventoryDomainError):
    """Raised when reservation exceeds available quantity"""
    pass

class InventoryNotFoundError(InventoryDomainError):
    """Raised when product not found in inventory"""
    pass
```

## Persistence Model (SQLAlchemy)

### Database Schema

**File**: `src/infrastructure/database/models.py`

```python
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

    def to_domain(self) -> 'Inventory':
        """Convert SQLAlchemy model to domain aggregate"""
        from src.domain.inventory import Inventory
        return Inventory(
            product_id=self.product_id,
            total_quantity=self.total_quantity,
            reserved_quantity=self.reserved_quantity,
            minimum_stock_level=self.minimum_stock_level
        )

    @staticmethod
    def from_domain(inventory: 'Inventory') -> 'InventoryModel':
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
```

**Database Indexes**:
- `product_id` (primary key on inventory table)
- `event_type` (for filtering events by type)
- `product_id` on event_log (for querying product history)

**Constraints**:
- `total_quantity >= 0` (enforced by domain, checked by DB)
- `reserved_quantity >= 0` (enforced by domain, checked by DB)
- `reserved_quantity <= total_quantity` (enforced by domain)

## API Schemas (Pydantic)

### Request Schemas

**File**: `src/infrastructure/api/schemas.py`

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class ReserveInventoryRequest(BaseModel):
    """Request to reserve inventory"""
    quantity: int = Field(..., gt=0, description="Quantity to reserve (must be positive)")
    order_id: str = Field(..., min_length=1, description="Order ID for idempotency")

    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than zero')
        return v

class ReleaseInventoryRequest(BaseModel):
    """Request to release reserved inventory"""
    quantity: int = Field(..., gt=0, description="Quantity to release")
    order_id: str = Field(..., min_length=1, description="Order ID")
    reason: str = Field(..., min_length=1, description="Reason for release")

class AdjustInventoryRequest(BaseModel):
    """Request to adjust inventory"""
    new_quantity: int = Field(..., ge=0, description="New total quantity (must be non-negative)")
    reason: str = Field(..., min_length=1, description="Reason for adjustment")
    adjusted_by: str = Field(..., min_length=1, description="User or system performing adjustment")

### Response Schemas

class InventoryResponse(BaseModel):
    """Response with current inventory status"""
    product_id: str
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    minimum_stock_level: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "PROD-12345",
                "total_quantity": 100,
                "reserved_quantity": 20,
                "available_quantity": 80,
                "minimum_stock_level": 10
            }
        }
    }

class OperationResult(BaseModel):
    """Generic operation result"""
    success: bool
    message: str
    inventory: InventoryResponse

class LowStockItem(BaseModel):
    """Item in low stock list"""
    product_id: str
    available_quantity: int
    minimum_stock_level: int
    shortfall: int  # minimum_stock_level - available_quantity

class LowStockResponse(BaseModel):
    """Response with low stock items"""
    items: list[LowStockItem]
    count: int

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "InsufficientStock",
                "detail": "Cannot reserve 10 units. Only 5 available.",
                "timestamp": "2025-12-24T10:30:00Z"
            }
        }
    }
```

## Data Relationships

### Entity Relationship Diagram

```
┌─────────────────┐
│   Inventory     │
├─────────────────┤
│ product_id (PK) │
│ total_quantity  │
│ reserved_qty    │
│ minimum_level   │
│ created_at      │
│ updated_at      │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│   EventLog      │
├─────────────────┤
│ id (PK)         │
│ event_type      │
│ product_id (FK) │
│ event_data      │
│ timestamp       │
└─────────────────┘
```

### Data Flow

```
API Request (Pydantic schema)
    ↓
Domain Command (dataclass)
    ↓
Inventory Aggregate (domain logic)
    ↓
Domain Events (dataclass)
    ↓
Repository → SQLAlchemy Model → Database
    ↓
Event Log → EventLogModel → Database
```

## Validation Rules

### Domain Level
- `total_quantity >= 0`
- `reserved_quantity >= 0`
- `reserved_quantity <= total_quantity`
- `available_quantity = total_quantity - reserved_quantity` (always true)
- `minimum_stock_level >= 0`

### API Level (Pydantic)
- Reserve quantity > 0
- Release quantity > 0
- Adjust new_quantity >= 0
- All string fields non-empty
- Order ID required for idempotency

### Database Level (SQLAlchemy)
- product_id unique and non-null
- Numeric fields non-null with defaults

## Migration Strategy

**Initial Schema** (Alembic migration):
```sql
CREATE TABLE inventory (
    product_id VARCHAR PRIMARY KEY,
    total_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    minimum_stock_level INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR NOT NULL,
    product_id VARCHAR NOT NULL,
    event_data TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_type ON event_log(event_type);
CREATE INDEX idx_product_id ON event_log(product_id);
```

## Type Mappings

| Domain Type | SQLAlchemy Type | Pydantic Type | JSON Type |
|-------------|-----------------|---------------|-----------|
| str (product_id) | String | str | string |
| int (quantities) | Integer | int | number |
| datetime | DateTime | datetime | string (ISO 8601) |
| Inventory | - (domain only) | InventoryResponse | object |
| Events | - (domain only) | - (internal) | object (in event_log) |

## Concurrency Handling

**Optimistic Locking**: Not used (complexity not justified)

**Pessimistic Locking**: SQLAlchemy `with_for_update()`
```python
inventory = session.query(InventoryModel).filter_by(
    product_id=product_id
).with_for_update().first()
```

**Transaction Isolation**: SQLite SERIALIZABLE (default for writes)

This ensures atomic updates without race conditions per spec.md FR-016 and SC-002.
