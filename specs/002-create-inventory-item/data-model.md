# Data Model: Create Inventory Item

**Feature**: 002-create-inventory-item
**Date**: 2025-12-25

## Overview

This document defines the data structures for the create inventory item feature. The feature extends the existing Inventory aggregate with creation capability, adding new command and event types while reusing existing entity structure.

## Domain Model Extensions

### Aggregate: Inventory (Extended)

**Existing State** (unchanged):
```python
product_id: str              # Unique product identifier
total_quantity: int          # Total physical stock
reserved_quantity: int       # Stock committed to orders
minimum_stock_level: int     # Reorder threshold
```

**Computed Properties** (unchanged):
```python
available_quantity: int      # total_quantity - reserved_quantity
```

**New Factory Method**:
```python
@classmethod
def create(
    cls,
    product_id: str,
    initial_quantity: int,
    minimum_stock_level: int
) -> tuple['Inventory', List[DomainEvent]]
```

**Creation Invariants**:
1. `product_id` MUST NOT be empty or whitespace-only
2. `initial_quantity` MUST be >= 0
3. `minimum_stock_level` MUST be >= 0
4. Created inventory MUST have `reserved_quantity = 0`
5. Created inventory MUST have `available_quantity = initial_quantity`

**Validation Rules**:
- Product ID uniqueness enforced at repository layer (database constraint)
- Negative quantities rejected with `InvalidQuantityError`
- Empty product_id rejected with `InvalidQuantityError` (or new `InvalidProductIdError`)

### Commands (New)

#### CreateInventory

Represents the intent to create a new inventory record.

**Structure**:
```python
@dataclass
class CreateInventory:
    """Command to create new inventory record"""
    product_id: str
    initial_quantity: int
    minimum_stock_level: int
```

**Validation**:
- `product_id`: non-empty string (min_length=1)
- `initial_quantity`: non-negative integer (>= 0)
- `minimum_stock_level`: non-negative integer (>= 0)

**Origin**: Sent from API layer when POST /v1/inventory request received

**Destination**: Processed by InventoryService.create_inventory()

### Events (New)

#### InventoryCreated

Immutable record that inventory was successfully created.

**Structure**:
```python
@dataclass
class InventoryCreated:
    """Event emitted when new inventory record is created"""
    product_id: str
    initial_quantity: int
    minimum_stock_level: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

**Emitted By**: Inventory.create() factory method

**Consumers**:
1. LocalEventPublisher (persists event)
2. StockLevelMonitor policy (checks for immediate low stock condition)
3. Future: External systems (analytics, notifications, etc.)

**Event Flow**:
```
API Request → CreateInventory command → Inventory.create() → InventoryCreated event → Event Publisher
                                                           ↓
                                                    LowStockDetected event (if applicable)
```

### Exceptions (Reuse Existing + One New)

**Existing Exceptions Reused**:
- `InvalidQuantityError`: Raised for negative quantities or empty product_id
- `InsufficientStockError`: NOT used in creation (only reserve operation)

**New Exception** (if needed):
```python
class InventoryAlreadyExistsError(Exception):
    """Raised when attempting to create inventory for product that already exists"""
    pass
```

**Exception Mapping** (Repository → Domain → Application → API):
```
SQLAlchemy IntegrityError → InventoryAlreadyExistsError → HTTP 409 Conflict
InvalidQuantityError → InvalidQuantityError → HTTP 422 Unprocessable Entity
```

## Application Layer

### Service Method (New)

**Signature**:
```python
def create_inventory(
    self,
    product_id: str,
    initial_quantity: int,
    minimum_stock_level: int
) -> Inventory
```

**Responsibilities**:
1. Validate inputs (delegate to domain)
2. Check for existing inventory (via repository)
3. Create new inventory using aggregate factory method
4. Persist via repository
5. Publish events via event publisher
6. Return created inventory entity

**Transaction Boundary**: Single database transaction (create + persist events)

**Error Handling**:
- Duplicate product → raise `InventoryAlreadyExistsError`
- Invalid inputs → raise `InvalidQuantityError`
- Database errors → propagate as-is (infrastructure concern)

## Infrastructure Layer

### API Schema (New)

#### CreateInventoryRequest

**Purpose**: Request body validation for POST /v1/inventory

**Structure**:
```python
class CreateInventoryRequest(BaseModel):
    """Request to create new inventory record"""
    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    initial_quantity: int = Field(..., ge=0, description="Initial stock quantity (non-negative)")
    minimum_stock_level: int = Field(..., ge=0, description="Minimum stock threshold (non-negative)")

    @field_validator('product_id')
    @classmethod
    def product_id_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Product ID cannot be whitespace only')
        return v.strip()
```

**Validation**:
- Pydantic performs automatic validation
- Custom validator ensures product_id is not whitespace-only
- Field constraints: min_length=1, ge=0 (greater than or equal)

#### Response Models (Reuse Existing)

**Success Response**: `OperationResult` (existing)
```python
{
    "success": true,
    "message": "Successfully created inventory for product PROD-123",
    "inventory": {
        "product_id": "PROD-123",
        "total_quantity": 100,
        "reserved_quantity": 0,
        "available_quantity": 100,
        "minimum_stock_level": 10
    }
}
```

**Error Responses**: `ErrorResponse` (existing)
```python
# 409 Conflict
{
    "error": "InventoryAlreadyExists",
    "detail": "Inventory record already exists for product PROD-123",
    "timestamp": "2025-12-25T10:30:00Z"
}

# 422 Validation Error
{
    "error": "ValidationError",
    "detail": "Initial quantity must be non-negative",
    "timestamp": "2025-12-25T10:30:00Z"
}
```

### Repository Method (New)

**Signature**:
```python
def create(self, inventory: Inventory) -> Inventory
```

**Responsibilities**:
1. Convert domain Inventory to database InventoryModel
2. Persist to database via SQLAlchemy session
3. Catch IntegrityError (unique constraint violation) → raise InventoryAlreadyExistsError
4. Refresh entity to get any DB-generated values
5. Return created domain entity

**Database Interaction**:
```python
# Pseudocode
db_model = InventoryModel(
    product_id=inventory.product_id,
    total_quantity=inventory.total_quantity,
    reserved_quantity=inventory.reserved_quantity,
    minimum_stock_level=inventory.minimum_stock_level
)
session.add(db_model)
try:
    session.commit()
except IntegrityError:
    session.rollback()
    raise InventoryAlreadyExistsError(f"Product {inventory.product_id} already exists")
session.refresh(db_model)
return to_domain_entity(db_model)
```

### Database Schema (Existing - Verify)

**Table**: `inventory`

**Expected Columns**:
```sql
product_id VARCHAR PRIMARY KEY (UNIQUE constraint)
total_quantity INTEGER NOT NULL
reserved_quantity INTEGER NOT NULL DEFAULT 0
minimum_stock_level INTEGER NOT NULL DEFAULT 0
-- Possibly: created_at, updated_at timestamps
```

**Constraints**:
- PRIMARY KEY or UNIQUE constraint on product_id
- NOT NULL constraints on quantity fields

**Action**: Verify existing schema matches expected structure; no migration needed if already compatible.

## State Transitions

### Creation Flow

```
[No Record]
    ↓ POST /v1/inventory
    ↓ CreateInventory command
    ↓ Inventory.create() validates
    ↓ Repository.create() persists
    ↓ InventoryCreated event emitted
    ↓
[Inventory Record Exists]
    product_id: "PROD-123"
    total_quantity: 100
    reserved_quantity: 0
    available_quantity: 100
    minimum_stock_level: 10
```

### Edge Case: Low Stock on Creation

If `initial_quantity < minimum_stock_level`:

```
Inventory.create()
    ↓ Emits InventoryCreated
    ↓ Checks low stock condition
    ↓ Emits LowStockDetected (if initial < minimum)
    ↓
Events: [InventoryCreated, LowStockDetected]
```

This is valid per spec edge cases - allows creating inventory that's immediately low on stock.

## Relationships

**No new entity relationships**. This feature works with the single Inventory aggregate.

**Event Relationships**:
- InventoryCreated → consumed by StockLevelMonitor policy
- LowStockDetected → may be emitted by StockLevelMonitor if created inventory is already low

## Data Validation Summary

| Field | Layer | Validation |
|-------|-------|------------|
| product_id | API | Pydantic: min_length=1, not whitespace |
| product_id | Domain | Not empty (ValueError if empty) |
| product_id | Database | UNIQUE constraint |
| initial_quantity | API | Pydantic: ge=0 (>= 0) |
| initial_quantity | Domain | >= 0 (InvalidQuantityError if negative) |
| minimum_stock_level | API | Pydantic: ge=0 (>= 0) |
| minimum_stock_level | Domain | >= 0 (InvalidQuantityError if negative) |

**Validation Strategy**: Defense in depth
- API layer: Fast fail with clear error messages (Pydantic)
- Domain layer: Business rule enforcement (invariants)
- Database layer: Data integrity constraints (UNIQUE)

## Examples

### Valid Creation

**Input**:
```json
{
    "product_id": "PROD-12345",
    "initial_quantity": 100,
    "minimum_stock_level": 10
}
```

**Result**:
```python
Inventory(
    product_id="PROD-12345",
    total_quantity=100,
    reserved_quantity=0,
    minimum_stock_level=10
)
Events: [InventoryCreated(product_id="PROD-12345", initial_quantity=100, minimum_stock_level=10)]
```

### Zero Initial Quantity (Valid)

**Input**:
```json
{
    "product_id": "PROD-99999",
    "initial_quantity": 0,
    "minimum_stock_level": 5
}
```

**Result**:
```python
Inventory(
    product_id="PROD-99999",
    total_quantity=0,
    reserved_quantity=0,
    minimum_stock_level=5
)
Events: [
    InventoryCreated(product_id="PROD-99999", initial_quantity=0, minimum_stock_level=5),
    LowStockDetected(product_id="PROD-99999", available_quantity=0, minimum_stock_level=5)
]
```

### Invalid: Negative Quantity

**Input**:
```json
{
    "product_id": "PROD-12345",
    "initial_quantity": -10,
    "minimum_stock_level": 10
}
```

**Result**: HTTP 422 Validation Error
```json
{
    "error": "ValidationError",
    "detail": "initial_quantity must be greater than or equal to 0"
}
```

### Invalid: Duplicate Product

**Input**:
```json
{
    "product_id": "PROD-EXISTING",
    "initial_quantity": 50,
    "minimum_stock_level": 10
}
```

**Result**: HTTP 409 Conflict
```json
{
    "error": "InventoryAlreadyExists",
    "detail": "Inventory record already exists for product PROD-EXISTING"
}
```
