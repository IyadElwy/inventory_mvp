# Feature Specification: Inventory Management REST API

**Feature Branch**: `001-inventory-rest-api`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Create a REST API for this microservice. It should have a modular project structure. It should use the latest stable version of FastAPI with Python 3.12. For the database use SQLite with SQLAlchemy as ORM. Use Pydantic models for data modelling. Write unit tests using pytest as well as mocks with unittest.mock. In the end, the whole application should run in a docker container, so we will need a Dockerfile."

## Clarifications

### Session 2025-12-25

- Q: When inventory operations emit events (InventoryReserved, InventoryReleased, etc.), what should happen if event publishing fails? → A: Roll back the inventory operation (transaction fails) - ensures consistency
- Q: If the same reservation request (same order_id, product_id, quantity) is submitted multiple times due to network retries, how should the system respond? → A: Return success with current state (idempotent) - safe for retries
- Q: When a LowStockDetected event is emitted, how should purchasing managers actually receive the notification? → A: Only queryable via GET /low-stock endpoint; no proactive notifications
- Q: How do products initially get into the inventory system with their starting quantities and minimum stock levels? → A: Products auto-created with zero quantities on first reserve/adjust attempt
- Q: When two requests try to reserve inventory for the same product simultaneously, what mechanism prevents race conditions? → A: Pessimistic locking with SELECT FOR UPDATE - blocks concurrent access

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check Inventory Availability (Priority: P1)

As an order processing system, I need to check if sufficient inventory is available for a product before creating an order, so that I can prevent overselling and ensure accurate stock levels.

**Why this priority**: This is the most critical operation as it prevents the fundamental business problem of selling products that are out of stock. Without this, the entire inventory management system fails its core purpose.

**Independent Test**: Can be fully tested by querying inventory status for a product and verifying the available quantity matches expected values. Delivers immediate value by providing real-time stock visibility.

**Acceptance Scenarios**:

1. **Given** a product with 100 total quantity and 20 reserved quantity, **When** I query inventory status, **Then** I receive available quantity of 80
2. **Given** a product that does not exist in inventory, **When** I query inventory status, **Then** I receive an appropriate error indicating product not found
3. **Given** multiple products in the system, **When** I query inventory for a specific product, **Then** I receive only that product's inventory data

---

### User Story 2 - Reserve Inventory for Orders (Priority: P1)

As an order processing system, I need to reserve inventory when an order is created, so that the stock is held for that order and not sold to others until the order is fulfilled or cancelled.

**Why this priority**: This is equally critical as checking availability because it ensures inventory atomicity - once reserved, stock cannot be double-allocated. This prevents race conditions in concurrent order scenarios.

**Independent Test**: Can be fully tested by reserving inventory for a product and verifying the reserved quantity increases while available quantity decreases accordingly. Delivers value by preventing overselling in multi-user scenarios.

**Acceptance Scenarios**:

1. **Given** a product with 50 available quantity, **When** I reserve 10 units, **Then** available quantity decreases to 40 and reserved quantity increases by 10
2. **Given** a product with 5 available quantity, **When** I attempt to reserve 10 units, **Then** the reservation fails with an insufficient stock error
3. **Given** a successful reservation, **When** the operation completes, **Then** an InventoryReserved event is emitted with product ID, quantity, and reservation details

---

### User Story 3 - Release Reserved Inventory (Priority: P2)

As an order processing system, I need to release previously reserved inventory when an order is cancelled or times out, so that the stock becomes available again for other orders.

**Why this priority**: While not as immediately critical as reservation, this is essential for maintaining accurate inventory levels and preventing "stuck" reservations that artificially reduce available stock.

**Independent Test**: Can be fully tested by first reserving inventory, then releasing it, and verifying available quantity returns to original value. Delivers value by ensuring cancelled orders don't permanently block inventory.

**Acceptance Scenarios**:

1. **Given** a product with 30 reserved quantity, **When** I release 10 units, **Then** available quantity increases by 10 and reserved quantity decreases by 10
2. **Given** a product with 5 reserved quantity, **When** I attempt to release 10 units, **Then** the release fails with an error indicating insufficient reserved quantity
3. **Given** a successful release, **When** the operation completes, **Then** an InventoryReleased event is emitted with product ID and quantity

---

### User Story 4 - Adjust Inventory Levels (Priority: P2)

As a warehouse manager, I need to manually adjust inventory quantities to correct discrepancies found during physical stock counts, so that the system reflects actual physical inventory.

**Why this priority**: This supports operational corrections and reconciliation, which is important but less frequent than order-driven operations. Most systems operate correctly without constant adjustments.

**Independent Test**: Can be fully tested by adjusting inventory to a specific total quantity and verifying the total and available quantities are updated correctly. Delivers value by enabling inventory reconciliation.

**Acceptance Scenarios**:

1. **Given** a product with 100 total quantity, **When** I adjust inventory to 120 total, **Then** total quantity becomes 120 and available quantity increases by 20
2. **Given** a product with 50 total and 20 reserved, **When** I adjust total quantity to 15, **Then** the adjustment fails because it would result in negative available quantity
3. **Given** a successful adjustment, **When** the operation completes, **Then** an InventoryAdjusted event is emitted with product ID, old quantity, and new quantity

---

### User Story 5 - Monitor Low Stock Alerts (Priority: P3)

As a purchasing manager, I need to query which products are below minimum stock thresholds, so that I can reorder inventory before running out of stock.

**Why this priority**: This is a valuable feature for proactive inventory management but not critical for day-to-day operations. The system can function without it, though less efficiently.

**Independent Test**: Can be fully tested by reducing a product's available quantity below its minimum threshold and verifying it appears in the low stock query results. Delivers value by enabling proactive restocking.

**Acceptance Scenarios**:

1. **Given** a product with minimum stock level of 20 and available quantity of 25, **When** inventory is reserved reducing available to 15, **Then** a LowStockDetected event is emitted
2. **Given** a product with minimum stock level of 10 and available quantity of 15, **When** I query low stock items, **Then** this product is not included in results
3. **Given** multiple products with low stock, **When** I query low stock items, **Then** I receive a list of all products below their minimum thresholds

---

### Edge Cases

- What happens when attempting to reserve inventory with a quantity of zero or negative number?
- Concurrent reservations for the same product are handled using pessimistic locking (SELECT FOR UPDATE) which blocks the second request until the first completes, ensuring atomic operations
- What happens when adjusting inventory would violate the invariant that reserved quantity cannot exceed total quantity?
- For GET requests on non-existent product IDs, the system returns 404 error; for reserve/adjust operations, the product is auto-created with zero quantities before processing the operation
- When the same reservation is attempted multiple times (same order_id, product_id, quantity), the system returns success with current inventory state without creating duplicate reservations, enabling safe client retries
- How are timestamp and audit trail requirements handled for inventory changes?
- If event publishing fails during an inventory operation, the entire operation is rolled back and returns an error to the caller, ensuring no state change occurs without corresponding event notification

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an API endpoint to query current inventory status for a product by product ID
- **FR-002**: System MUST provide an API endpoint to reserve inventory for a product with specified quantity
- **FR-003**: System MUST provide an API endpoint to release previously reserved inventory for a product
- **FR-004**: System MUST provide an API endpoint to manually adjust total inventory quantity for a product
- **FR-005**: System MUST provide an API endpoint to query all products with stock below minimum threshold
- **FR-006**: System MUST validate that reservation quantity does not exceed available quantity before confirming
- **FR-007**: System MUST validate that release quantity does not exceed currently reserved quantity
- **FR-008**: System MUST validate that inventory adjustments do not violate the invariant: AvailableQuantity = TotalQuantity - ReservedQuantity
- **FR-009**: System MUST emit InventoryReserved event when reservation succeeds
- **FR-010**: System MUST emit InventoryReleased event when release succeeds
- **FR-011**: System MUST emit InventoryAdjusted event when adjustment succeeds
- **FR-012**: System MUST emit LowStockDetected event when available quantity falls below minimum stock level
- **FR-013**: System MUST return appropriate HTTP status codes for success (200, 201) and error conditions (400, 404, 409)
- **FR-014**: System MUST validate all request payloads and reject invalid data with clear error messages
- **FR-015**: System MUST persist inventory state across system restarts
- **FR-016**: System MUST handle concurrent requests safely without race conditions or data corruption
- **FR-017**: System MUST treat inventory operations and event publishing as atomic transactions - if event publishing fails, the inventory operation MUST be rolled back to ensure consistency
- **FR-018**: System MUST implement idempotent reservation operations - duplicate requests with the same order_id, product_id, and quantity MUST return success with current state without creating duplicate reservations
- **FR-019**: System MUST auto-create product inventory records with zero quantities and default minimum stock level when a reserve or adjust operation is attempted on a non-existent product

### Domain Model (CQRS + Event Sourcing)

#### Bounded Context
- **Context Name**: Inventory Management
- **Responsibility**: Track and manage product stock levels, handle reservations for orders, and monitor low stock conditions
- **Boundaries**: Does NOT include product catalog, order management, pricing, or fulfillment

#### Aggregate: Inventory
- **Aggregate Root**: Inventory (identified by ProductId)
- **State**:
  - ProductId: string (unique identifier)
  - TotalQuantity: integer (total stock on hand)
  - ReservedQuantity: integer (stock held for pending orders)
  - MinimumStockLevel: integer (threshold for low stock alerts)
- **Derived State**:
  - AvailableQuantity: integer = TotalQuantity - ReservedQuantity
- **Invariants**:
  - AvailableQuantity ≥ 0 (cannot have negative available stock)
  - ReservedQuantity ≤ TotalQuantity (cannot reserve more than total)
  - AvailableQuantity = TotalQuantity - ReservedQuantity (calculated property consistency)
  - TotalQuantity ≥ 0 (cannot have negative total quantity)
  - ReservedQuantity ≥ 0 (cannot have negative reservations)
  - MinimumStockLevel ≥ 0 (threshold must be non-negative)

#### Commands
Commands represent write operations (state-changing intents):

1. **ReserveInventory**
   - Input: ProductId (string), Quantity (integer), OrderId (string)
   - Validation: Quantity > 0, AvailableQuantity >= Quantity
   - Success Event: InventoryReserved
   - Failure: InsufficientStockError if not enough available
   - Idempotency: Same OrderId + ProductId + Quantity = success without duplicate reservation

2. **ReleaseInventory**
   - Input: ProductId (string), Quantity (integer), OrderId (string), Reason (string)
   - Validation: Quantity > 0, ReservedQuantity >= Quantity
   - Success Event: InventoryReleased
   - Failure: InvalidQuantityError if quantity exceeds reserved
   - Use Cases: Order cancellation, payment failure, order timeout

3. **AdjustInventory**
   - Input: ProductId (string), NewTotalQuantity (integer), Reason (string), AdjustedBy (string)
   - Validation: NewTotalQuantity >= 0, NewTotalQuantity >= ReservedQuantity
   - Success Event: InventoryAdjusted
   - Failure: InvalidQuantityError if new total < reserved
   - Use Cases: Physical stock count, damaged goods, receiving shipment

#### Events
Events represent facts about state changes (past tense):

1. **InventoryReserved**
   - ProductId: string
   - Quantity: integer (amount reserved)
   - OrderId: string
   - Timestamp: datetime
   - AvailableQuantity: integer (after reservation)
   - ReservedQuantity: integer (after reservation)

2. **InventoryReleased**
   - ProductId: string
   - Quantity: integer (amount released)
   - OrderId: string
   - Reason: string
   - Timestamp: datetime
   - AvailableQuantity: integer (after release)
   - ReservedQuantity: integer (after release)

3. **InventoryAdjusted**
   - ProductId: string
   - OldQuantity: integer (previous total)
   - NewQuantity: integer (new total)
   - Reason: string
   - AdjustedBy: string
   - Timestamp: datetime
   - AvailableQuantity: integer (after adjustment)

4. **LowStockDetected**
   - ProductId: string
   - AvailableQuantity: integer (current available)
   - MinimumStockLevel: integer (threshold)
   - Timestamp: datetime

#### Policies
Policies are business rules that react to events:

1. **StockLevelMonitor Policy**
   - Trigger: After InventoryReserved or InventoryAdjusted events
   - Condition: AvailableQuantity < MinimumStockLevel
   - Action: Emit LowStockDetected event
   - Purpose: Proactive notification of low stock for reordering

#### Read Models
Read models are optimized views for queries (CQRS read side):

1. **InventoryStatusReadModel**
   - Purpose: Display current inventory on product pages
   - Data: ProductId, TotalQuantity, ReservedQuantity, AvailableQuantity, MinimumStockLevel
   - Updated By: All inventory events
   - Query Endpoint: GET /v1/inventory/{product_id}

2. **LowStockListReadModel**
   - Purpose: Admin dashboard showing products needing reorder
   - Data: List of ProductId where AvailableQuantity < MinimumStockLevel
   - Updated By: InventoryReserved, InventoryAdjusted, LowStockDetected events
   - Query Endpoint: GET /v1/inventory/low-stock

#### Event Sourcing Architecture

**Event-Driven State Changes**:
- All state modifications go through commands that emit events
- Events are the source of truth for state reconstruction
- No direct state mutation outside command handlers

**Event Persistence**:
- All events MUST be persisted before command completes
- Events stored in append-only event log
- Event publishing and state persistence are atomic (both succeed or both rollback)

**Idempotency Guarantees**:
- ReserveInventory: Same OrderId + ProductId + Quantity = no duplicate reservation, return current state
- Commands include correlation IDs for de-duplication
- Safe for network retries

**Event Ordering**:
- Events for same Aggregate (ProductId) are strictly ordered by timestamp
- Cross-aggregate events have no ordering guarantees
- Event replay reconstructs aggregate state in chronological order

#### Business Logic Rules

**Stock Reservation Validation**:
- MUST check AvailableQuantity >= RequestedQuantity before reserving
- Fail with InsufficientStockError (HTTP 409) if insufficient
- Use pessimistic locking (SELECT FOR UPDATE) to prevent race conditions

**Stock Release Conditions**:
- Order cancellation by customer
- Payment processing failure
- Order timeout (no payment within deadline)
- Release quantity MUST NOT exceed currently reserved quantity

**Manual Inventory Adjustment Rules**:
- Only authorized warehouse managers can adjust
- Requires Reason (e.g., "Physical count", "Damaged goods")
- Requires AdjustedBy identifier for audit trail
- Cannot adjust below currently reserved quantity
- All adjustments logged as events for compliance

**Low Stock Threshold Behavior**:
- Triggered when AvailableQuantity falls below MinimumStockLevel
- LowStockDetected event emitted automatically
- Purchasing managers query GET /low-stock endpoint (pull-based, not push notifications)

**Concurrent Reservation Handling**:
- Pessimistic locking with SELECT FOR UPDATE on aggregate row
- Second request blocks until first completes
- Ensures atomic read-modify-write operations
- Prevents double allocation across concurrent requests

**Double Reservation Prevention**:
- Idempotency key: OrderId + ProductId + Quantity
- Duplicate requests return success with current inventory state
- No duplicate InventoryReserved events for same order

#### Integration Contracts

**Order Service Integration** (Command Source):
- Sends: ReserveInventory command when order created
- Sends: ReleaseInventory command when order cancelled/failed
- Expects: Synchronous HTTP response (success/failure)
- Error Handling: Receives HTTP 409 if insufficient stock, HTTP 404 if product not found

**Notification Service Integration** (Event Consumer):
- Receives: LowStockDetected events (for future proactive notifications)
- Receives: All inventory events for audit logging
- Delivery: Asynchronous event subscription (fire-and-forget from inventory service perspective)
- Note: Currently low stock monitoring is pull-based via GET /low-stock, but events enable future push notifications

**Event Publishing Requirements**:
- Events published to message bus after successful state persistence
- Publishing MUST be part of atomic transaction with state change
- If event publishing fails, entire operation (state change + event) rolls back
- Ensures consistency between inventory state and published events

**API Contracts**:
- POST /v1/inventory/{product_id}/reserve: ReserveInventoryRequest → OperationResult
- POST /v1/inventory/{product_id}/release: ReleaseInventoryRequest → OperationResult
- PUT /v1/inventory/{product_id}: AdjustInventoryRequest → OperationResult
- GET /v1/inventory/{product_id}: → InventoryResponse
- GET /v1/inventory/low-stock: → LowStockListResponse

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Order processing systems can successfully check inventory availability and receive responses in under 100 milliseconds for 95% of requests
- **SC-002**: Inventory reservation operations complete atomically with no possibility of double-allocation across 1000 concurrent requests
- **SC-003**: Inventory state remains consistent after system restart, with zero data loss for committed transactions
- **SC-004**: 100% of inventory modifications (reserve, release, adjust) are recorded as events for audit trail purposes
- **SC-005**: Low stock alerts are triggered within 1 second of inventory falling below minimum threshold
- **SC-006**: API consumers receive clear, actionable error messages for 100% of invalid requests (bad product ID, insufficient stock, invalid quantity)
- **SC-007**: System successfully handles 100 requests per second without degradation in response time
- **SC-008**: All business invariants (AvailableQuantity ≥ 0, ReservedQuantity ≤ TotalQuantity) are enforced with zero violations across all operations

## Assumptions

- Product IDs are provided by an external product catalog system (not managed by this microservice)
- Authentication and authorization are handled by an external API gateway or authentication service
- The system operates in a single-region deployment (no multi-region consistency requirements)
- Inventory units are whole numbers (no fractional quantities)
- Currency and pricing are managed by separate services (this service only tracks quantities)
- The minimum stock level for each product defaults to 0 when auto-created; can be updated via adjust operations
- Event consumers (for InventoryReserved, InventoryReleased, etc.) are external systems that will subscribe to these events for audit and integration purposes
- Network reliability between API consumers and this service is acceptable for synchronous HTTP requests
- Low stock monitoring is pull-based: purchasing managers or dashboards poll the GET /low-stock endpoint rather than receiving proactive push notifications

## Out of Scope

- Product catalog management (creating products, product details, categories)
- User authentication and authorization
- Order management (this service only manages inventory, not orders)
- Payment processing
- Shipping and fulfillment
- Multi-warehouse or multi-location inventory tracking
- Batch import/export of inventory data
- Historical reporting and analytics (only current state is managed)
- Inventory forecasting or demand prediction
- Purchase order management for restocking
