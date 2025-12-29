# Research: Inventory Management REST API

**Feature**: 001-inventory-rest-api
**Date**: 2025-12-24
**Phase**: Phase 0 - Research & Technology Decisions

## Technology Stack Decisions

### Python 3.12 + FastAPI

**Decision**: Use Python 3.12 with FastAPI framework for REST API implementation

**Rationale**:
- Python 3.12 provides latest performance improvements (PEP 669 monitoring, faster error messages)
- FastAPI is async-first framework ideal for I/O-bound operations (database queries)
- Built-in Pydantic integration for request/response validation aligns with constitution's API Contract Discipline
- Automatic OpenAPI/Swagger documentation generation satisfies constitution requirement
- Type hints and async/await support modern Python development practices
- Large ecosystem for testing (pytest), ORM (SQLAlchemy), and containerization (Docker)

**Alternatives Considered**:
- **Flask**: Simpler but requires more boilerplate for async, validation, and API docs
- **Django REST Framework**: Full-featured but heavy for microservice, includes ORM coupling we don't need
- **FastAPI chosen**: Best balance of performance, developer experience, and automatic API documentation

### SQLite + SQLAlchemy ORM

**Decision**: Use SQLite database with SQLAlchemy 2.0 ORM

**Rationale**:
- SQLite provides zero-configuration embedded database suitable for single-service deployment
- File-based storage simplifies Docker containerization (no separate database container needed)
- Atomic transactions support concurrency requirements (spec.md SC-002, FR-016)
- SQLAlchemy 2.0 provides mature ORM with async support, migration tools (Alembic)
- Repository pattern can abstract SQLAlchemy details from domain layer (DDD compliance)

**Alternatives Considered**:
- **PostgreSQL**: More robust for production but adds deployment complexity, overkill for MVP
- **In-memory dict**: Simpler but lacks persistence (violates spec.md FR-015, SC-003)
- **SQLite chosen**: Simplest solution that meets all persistence and concurrency requirements

**Concurrency Strategy**: Use SQLAlchemy's session-level locking or SELECT FOR UPDATE to prevent race conditions on inventory updates

### Pydantic for Data Modeling

**Decision**: Use Pydantic v2 for request/response schemas and validation

**Rationale**:
- Pydantic is FastAPI's native validation library (tight integration)
- V2 provides significant performance improvements over v1
- Declarative schema definition with automatic validation at API boundaries
- Supports OpenAPI schema generation for API documentation
- Type hints provide IDE support and runtime validation

**Alternatives Considered**:
- **Marshmallow**: Separate validation library, less integrated with FastAPI
- **Manual validation**: Error-prone, verbose, doesn't generate API docs
- **Pydantic chosen**: Industry standard for FastAPI, meets all validation needs

### Pytest + unittest.mock for Testing

**Decision**: Use pytest as test framework with unittest.mock for mocking

**Rationale**:
- pytest is Python's most popular testing framework with rich plugin ecosystem
- Fixtures support dependency injection for test setup
- Parametrized tests reduce duplication for edge cases
- unittest.mock (standard library) provides mocking without external dependencies
- Supports async tests for FastAPI endpoints (pytest-asyncio plugin)

**Test Organization**:
- `tests/unit/`: Domain logic tests (aggregates, commands, events, policies)
- `tests/integration/`: Application service tests with real database (in-memory SQLite)
- `tests/contract/`: API endpoint tests with TestClient

**Mocking Strategy**:
- Mock EventPublisher in unit tests to verify events emitted
- Mock Repository in application tests to isolate service logic
- Use real database (in-memory SQLite) for integration tests
- Use TestClient (no mocks) for contract tests

### Docker Containerization

**Decision**: Multi-stage Dockerfile with Alpine Linux base

**Rationale**:
- Multi-stage build separates dependencies (pip install) from runtime for smaller image
- Alpine Linux provides minimal base image (~5MB vs ~100MB for Debian)
- Python 3.12-alpine official image available
- Container includes SQLite binary (no external database needed)

**Dockerfile Structure**:
```dockerfile
# Stage 1: Dependencies
FROM python:3.12-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Alternatives Considered**:
- **Debian-based image**: Larger but more compatible with some packages
- **Docker Compose**: Overkill for single-service with embedded database
- **Alpine chosen**: Smallest image size, sufficient for our dependencies

## Architectural Patterns

### Domain-Driven Design Implementation

**Decision**: Implement DDD with clear layer separation (domain, application, infrastructure)

**Pattern Decisions**:

1. **Aggregate Root**: Inventory class in `src/domain/inventory.py`
   - Enforces invariants: `AvailableQuantity = TotalQuantity - ReservedQuantity`
   - Methods: `reserve()`, `release()`, `adjust()` return events
   - No setters - only command methods that validate and return events

2. **Command Pattern**: Dataclasses in `src/domain/commands.py`
   - `ReserveInventory`, `ReleaseInventory`, `AdjustInventory`
   - Immutable with validation in `__post_init__`

3. **Event Pattern**: Dataclasses in `src/domain/events.py`
   - `InventoryReserved`, `InventoryReleased`, `InventoryAdjusted`, `LowStockDetected`
   - Include timestamp, product_id, and event-specific data

4. **Repository Pattern**: Abstract base class + SQLAlchemy implementation
   - `InventoryRepository` (abstract) in `src/application/`
   - `SQLAlchemyInventoryRepository` in `src/infrastructure/database/`
   - Methods: `get()`, `save()`, `find_low_stock()`

5. **Policy Pattern**: `StockLevelMonitor` in `src/application/policies/`
   - Subscribes to inventory events
   - Emits `LowStockDetected` when `AvailableQuantity < MinimumStockLevel`

**Rationale**: Strict layer separation prevents infrastructure leakage into business logic, enables testing in isolation, and allows technology swaps without domain changes.

### Event-Driven Architecture (Simplified)

**Decision**: In-memory event publisher for MVP, designed for future async messaging

**Implementation**:
- `EventPublisher` interface in `src/application/event_publisher.py`
- `LocalEventPublisher` implementation in `src/infrastructure/events/`
- Events published synchronously during request handling
- Policies react to events within same transaction

**Future Evolution**:
- Replace `LocalEventPublisher` with `MessageQueuePublisher` (RabbitMQ, Kafka)
- Policies become separate services subscribing to event stream
- No domain or application code changes needed

**Rationale**: Start simple with synchronous events, but design for eventual async evolution without refactoring domain logic.

### API Design Patterns

**Decision**: RESTful JSON API with standard HTTP methods

**Endpoint Design**:
- `GET /v1/inventory/{product_id}` - Query inventory status
- `POST /v1/inventory/{product_id}/reserve` - Reserve inventory
- `POST /v1/inventory/{product_id}/release` - Release inventory
- `PUT /v1/inventory/{product_id}` - Adjust inventory
- `GET /v1/inventory/low-stock` - Query low stock items

**HTTP Methods**:
- GET for queries (idempotent, no side effects)
- POST for commands (non-idempotent state changes)
- PUT for replacements (idempotent adjustments)

**Status Codes**:
- 200 OK - Successful query or state change
- 201 Created - New inventory record created
- 400 Bad Request - Invalid input (negative quantity, etc.)
- 404 Not Found - Product not found
- 409 Conflict - Business rule violation (insufficient stock)

**Rationale**: Standard REST conventions make API predictable and easy to integrate with external systems.

## Concurrency & Data Integrity

**Decision**: Database-level locking for atomic inventory updates

**Strategy**:
- Use SQLAlchemy's `with_for_update()` for SELECT FOR UPDATE queries
- Lock inventory row during reserve/release/adjust operations
- Prevents race conditions where two requests reserve same inventory simultaneously

**Example**:
```python
# In repository
inventory = session.query(InventoryModel).filter_by(product_id=product_id).with_for_update().first()
```

**Transaction Isolation**:
- SQLite default isolation (SERIALIZABLE for writes)
- Each API request = single transaction
- Rollback on validation failure or exception

**Rationale**: Database locking is simplest solution for concurrency without distributed lock managers. SQLite's write serialization prevents corruption.

## Testing Strategy

**Decision**: Test Pyramid with focus on unit tests

**Test Distribution**:
- **70% Unit Tests**: Domain logic (aggregates, commands, events, policies)
  - Fast, no I/O, 100% code coverage goal
  - Mock all external dependencies

- **20% Integration Tests**: Application services with real database
  - Verify workflows (reserve → event → policy → low stock detection)
  - Use in-memory SQLite (`:memory:`) for speed

- **10% Contract Tests**: API endpoints with TestClient
  - Verify request/response schemas
  - Validate HTTP status codes and error messages

**Test-First Process** (per constitution):
1. Write failing test for requirement
2. Run test → RED (fails)
3. Write minimal implementation → GREEN (passes)
4. Refactor → tests still GREEN

**Rationale**: Inverted pyramid (more unit tests than integration/contract) provides fast feedback and high confidence with minimal execution time.

## Deployment Configuration

**Decision**: Environment-based configuration with sensible defaults

**Configuration Management**:
- Environment variables for runtime config (DATABASE_PATH, LOG_LEVEL)
- Pydantic Settings for typed configuration with validation
- Defaults for development (SQLite file, DEBUG logging)

**Docker Volume**:
- Mount `/app/data` for SQLite database persistence
- Ensures data survives container restarts (spec.md SC-003)

**Example**:
```bash
docker run -v ./data:/app/data -e DATABASE_PATH=/app/data/inventory.db inventory-api
```

**Rationale**: 12-factor app principles - configuration in environment, same image for dev/prod.

## Open Questions Resolved

None - all technical decisions specified in user input and clarified through research.

## Next Steps

Proceed to Phase 1:
- Generate `data-model.md` with SQLAlchemy and Pydantic schemas
- Create API contracts in `contracts/` directory (OpenAPI specification)
- Write `quickstart.md` for local development setup
