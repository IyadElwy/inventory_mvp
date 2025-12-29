# Research: Create Inventory Item

**Feature**: 002-create-inventory-item
**Date**: 2025-12-25
**Status**: Complete

## Overview

This document captures research findings for implementing the POST endpoint to create inventory items. Since the feature extends an existing, well-established codebase with clear DDD patterns, research focuses on consistency with existing patterns rather than exploring unknowns.

## Research Questions

### 1. How to Handle Duplicate Product Creation?

**Decision**: Use database-level UNIQUE constraint + application-level exception handling

**Rationale**:
- Existing codebase uses SQLAlchemy with models that include unique constraints
- Database-level enforcement prevents race conditions from concurrent requests (addresses edge case from spec)
- Application catches IntegrityError and translates to domain exception (AlreadyExistsError) for clean error handling
- Returns HTTP 409 Conflict per REST best practices for duplicate resource creation

**Alternatives Considered**:
- Check-then-insert pattern: Rejected due to race condition vulnerability
- Optimistic locking: Rejected as overkill for creation operation
- Application-level uniqueness check only: Rejected because doesn't prevent race conditions

**Implementation Pattern** (from existing codebase):
```python
# Database model already has unique constraint on product_id
# Repository catches IntegrityError and raises domain exception
# Service layer propagates domain exception
# API layer maps exception to HTTP 409
```

### 2. Should CreateInventory Be a Static Factory Method or Instance Method?

**Decision**: Static factory method (class method) on Inventory aggregate

**Rationale**:
- Creating new aggregate instances should not require an existing instance
- Follows domain-driven design aggregate creation patterns
- Consistent with common DDD practice (factories for complex creation)
- Clearer intent: `Inventory.create(...)` vs `inventory = Inventory(...)`
- Allows validation and event emission during creation

**Alternatives Considered**:
- Direct constructor: Rejected because doesn't allow pre-creation validation or event emission
- Separate Factory class: Rejected as unnecessary complexity for simple creation

**Implementation Pattern**:
```python
@classmethod
def create(cls, product_id: str, initial_quantity: int, minimum_stock_level: int) -> tuple['Inventory', List[Event]]:
    """Factory method to create new inventory record with validation."""
    # Validate inputs
    # Create instance
    # Emit InventoryCreated event
    # Check for low stock condition
    # Return (instance, events)
```

### 3. Event Design: What Data Should InventoryCreated Contain?

**Decision**: Include product_id, initial_quantity, minimum_stock_level (creation parameters)

**Rationale**:
- Events should be immutable records of what happened
- Include sufficient data for event handlers without requiring additional queries
- Matches pattern of existing events (InventoryReserved includes product_id and quantity)
- Enables event sourcing or audit trails if needed in future
- Keeps events self-contained and decoupled from aggregate state

**Alternatives Considered**:
- Minimal event (product_id only): Rejected because lacks context for handlers
- Full snapshot (all aggregate fields): Rejected because includes derived values (available_quantity)

**Implementation Pattern**:
```python
@dataclass
class InventoryCreated:
    product_id: str
    initial_quantity: int
    minimum_stock_level: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### 4. Repository Method Signature: Return Created Entity or Success Boolean?

**Decision**: Return created Inventory entity

**Rationale**:
- Consistent with existing repository.get() pattern (returns entity)
- Enables immediate use of created entity without additional query
- Supports "read your writes" consistency
- Provides all fields including database-generated values if any

**Alternatives Considered**:
- Return None on success: Rejected because requires additional query to get created entity
- Return product_id only: Rejected because service needs full entity for response

**Implementation Pattern**:
```python
def create(self, inventory: Inventory) -> Inventory:
    """Persist new inventory record and return created entity."""
    # Convert to database model
    # Persist to database
    # Refresh to get any DB-generated values
    # Return domain entity
```

### 5. Input Validation: Where Should Zero Quantity Be Validated?

**Decision**: Allow zero for both initial_quantity and minimum_stock_level (non-negative validation only)

**Rationale**:
- Spec specifies "non-negative" which includes zero (FR-004, FR-005)
- Valid business case: Product exists but has zero stock on creation
- Valid business case: Some products may have zero minimum stock requirement
- Pydantic validator uses `ge=0` (greater than or equal to zero)
- Simpler validation logic, fewer edge cases

**Alternatives Considered**:
- Require positive (gt=0) initial_quantity: Rejected because spec explicitly allows zero
- Different rules for initial vs minimum: Rejected as unnecessarily complex

**Implementation Pattern**:
```python
class CreateInventoryRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    initial_quantity: int = Field(..., ge=0)  # >= 0
    minimum_stock_level: int = Field(..., ge=0)  # >= 0
```

## Technology Patterns

### FastAPI Best Practices for POST Endpoints

**Pattern**: Use 201 Created status code with response body containing created resource

**Reference**: Existing codebase uses `response_model` and returns data directly; FastAPI handles status codes via `status_code` parameter

**Application**:
```python
@router.post(
    "/inventory",
    response_model=OperationResult,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Product already exists"},
        422: {"description": "Validation error"}
    }
)
```

### SQLAlchemy Uniqueness Constraint

**Pattern**: Existing database models use SQLAlchemy declarative with Column constraints

**Reference**: From existing codebase `database/models.py`

**Application**: Database model likely already has unique constraint on product_id column; verify and use existing constraint

### Pydantic Validation

**Pattern**: Existing schemas use Pydantic v2 with Field validators

**Reference**: `AdjustInventoryRequest` uses `Field(..., ge=0)` for non-negative validation

**Application**: Follow same pattern for CreateInventoryRequest validation

## Dependencies Analysis

**New Dependencies Required**: None

**Existing Dependencies Used**:
- FastAPI: API endpoint definition
- Pydantic: Request/response validation
- SQLAlchemy: Database persistence
- pytest: Test framework

All required functionality exists in current dependency versions.

## Integration Points

### 1. Database Schema

**Consideration**: Does inventory table need modification?

**Finding**: No schema changes required. Existing inventory table should support:
- product_id (VARCHAR, UNIQUE)
- total_quantity (INTEGER)
- reserved_quantity (INTEGER, default 0)
- minimum_stock_level (INTEGER, default 0)

**Action**: Verify existing schema compatibility; no migration needed if schema already supports these fields

### 2. Event Publisher

**Consideration**: How to publish InventoryCreated event?

**Finding**: Existing `LocalEventPublisher` pattern used by other operations

**Action**: Follow existing pattern - InventoryService receives event_publisher via dependency injection, publishes events after successful creation

### 3. API Route Organization

**Consideration**: Where to place POST /inventory endpoint in routes.py?

**Finding**: Existing routes.py has:
- GET /inventory/{product_id} - retrieve
- POST /inventory/{product_id}/reserve - reserve
- POST /inventory/{product_id}/release - release
- PUT /inventory/{product_id} - adjust

**Action**: Add POST /inventory (collection endpoint) before GET /inventory/{product_id} (item endpoint) for logical grouping

## Open Questions Resolved

All questions from spec edge cases addressed:

1. **Product ID special characters**: Allowed (no character restrictions)
2. **Concurrent creation**: Handled via database UNIQUE constraint
3. **Minimum stock > initial quantity**: Allowed (valid scenario)
4. **Maximum limits**: None (accept any non-negative integer)

## Summary

Implementation is straightforward because:
1. No new dependencies required
2. All patterns exist in codebase
3. No database schema changes needed
4. Clean extension of existing DDD structure
5. No ambiguous technical decisions

Next phase can proceed directly to data model and contract design.
