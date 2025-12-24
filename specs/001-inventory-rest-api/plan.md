# Implementation Plan: Inventory Management REST API

**Branch**: `001-inventory-rest-api` | **Date**: 2025-12-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-inventory-rest-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a REST API microservice for inventory management that handles stock reservations, releases, adjustments, and low-stock monitoring. The system implements Domain-Driven Design with the Inventory aggregate managing consistency boundaries, command/event patterns for state changes, and CQRS for read optimization. Technical approach uses Python 3.12 with FastAPI framework, SQLite database with SQLAlchemy ORM, Pydantic for data validation, pytest for testing, and Docker containerization.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI (latest stable), SQLAlchemy, Pydantic
**Storage**: SQLite with SQLAlchemy ORM
**Testing**: pytest with unittest.mock for mocking
**Target Platform**: Linux server (Docker container)
**Project Type**: single (microservice)
**Performance Goals**: 100 requests/second, <100ms p95 response time
**Constraints**: Atomic operations for concurrency, zero data loss on restart
**Scale/Scope**: Single microservice managing inventory for product catalog

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Domain-Driven Design (DDD) Compliance**:
- [x] **Aggregates**: Inventory aggregate with boundaries (ProductId), invariants (AvailableQuantity ≥ 0, ReservedQuantity ≤ TotalQuantity)
- [x] **Commands**: ReserveInventory, ReleaseInventory, AdjustInventory with validation rules (spec.md FR-006, FR-007, FR-008)
- [x] **Events**: InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected (spec.md FR-009 to FR-012)
- [x] **Policies**: StockLevelMonitor policy reacts to inventory changes and emits LowStockDetected events
- [x] **Read Models**: InventoryStatusReadModel (query endpoint), LowStockListReadModel (low stock query)
- [x] **External Systems**: Product catalog assumed external (spec.md Assumptions), Order service sends commands via API
- [x] **User**: Assumed handled by external auth service (spec.md Assumptions - API gateway handles auth)

**II. Modular Architecture Compliance**:
- [x] **Module boundaries**: Three layers (domain, application, infrastructure) with clear responsibilities
- [x] **Inward dependencies**: infrastructure → application → domain (see Project Structure)
- [x] **Domain isolation**: domain/ has no imports from application/ or infrastructure/ layers
- [x] **Explicit interfaces**: Commands/Events for communication, EventPublisher interface for infrastructure
- [x] **Dependencies justified**: Repository pattern needed for persistence abstraction, documented in structure

**III. Test-First Development Compliance**:
- [x] **Test strategy**: Unit tests (domain), integration tests (application workflows), contract tests (API)
- [x] **TDD process**: Tests in Phase 2 tasks will be written before implementation code
- [x] **Mock strategy**: unittest.mock for external dependencies (database, event publisher)
- [x] **Test coverage**: All three layers covered (tests/unit/, tests/integration/, tests/contract/)

**IV. API Contract Discipline Compliance**:
- [x] **Schemas defined**: Pydantic models in infrastructure/api/schemas.py for requests/responses
- [x] **Input validation**: FastAPI + Pydantic validate at API boundaries (infrastructure layer)
- [x] **Error responses**: HTTP status codes defined in spec.md FR-013 (200, 201, 400, 404, 409)
- [x] **API versioning**: Start with /v1/ prefix, increment for breaking changes
- [x] **Auto-generated docs**: FastAPI generates OpenAPI/Swagger docs automatically

**V. Simplicity First Compliance**:
- [x] **Simplest approach**: Direct REST API with SQLite (no unnecessary message queues, caching layers, or microservice splitting)
- [x] **Justified patterns**: Repository for persistence abstraction, EventPublisher for testability
- [x] **Dependencies evaluated**: FastAPI (industry standard), SQLAlchemy (mature ORM), pytest (standard testing)
- [x] **Deviations documented**: Repository pattern adds indirection - see Complexity Tracking below

---

**Post-Design Re-evaluation** (after Phase 1):

✅ **All constitutional principles verified**:
- DDD elements fully defined in data-model.md (Aggregate, Commands, Events, Policies, Read Models)
- Layered architecture implemented with strict dependency flow (infrastructure → application → domain)
- Test strategy documented in quickstart.md with TDD workflow
- API contracts defined in contracts/openapi.yaml with Pydantic validation
- Complexity justified in Complexity Tracking section

**Gate Status**: **PASS** - Ready to proceed to task generation (`/speckit.tasks`)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── domain/              # Domain layer (aggregates, entities, value objects)
│   ├── inventory.py     # Inventory aggregate
│   ├── commands.py      # Command definitions
│   ├── events.py        # Event definitions
│   └── exceptions.py    # Domain exceptions
├── application/         # Application layer (use cases, services)
│   ├── inventory_service.py  # Inventory business logic
│   ├── event_publisher.py    # Event publishing interface
│   └── policies/             # Business policies
│       └── stock_monitor.py  # StockLevelMonitor policy
├── infrastructure/      # Infrastructure layer (persistence, API)
│   ├── database/
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── repository.py # Repository pattern for Inventory
│   │   └── session.py   # Database session management
│   ├── api/
│   │   ├── routes.py    # FastAPI route definitions
│   │   ├── schemas.py   # Pydantic request/response models
│   │   └── dependencies.py # Dependency injection
│   └── events/
│       └── local_publisher.py # In-memory event publisher
└── main.py              # FastAPI application entry point
└── sqlite.db              # The sqlite db

tests/
├── unit/                # Domain and application logic tests
│   ├── test_inventory_aggregate.py
│   ├── test_inventory_service.py
│   └── test_stock_monitor_policy.py
├── integration/         # Service layer integration tests
│   ├── test_inventory_workflows.py
│   └── test_event_publishing.py
└── contract/            # API contract tests
    └── test_inventory_api.py

Dockerfile               # Container definition
requirements.txt         # Python dependencies
pytest.ini              # pytest configuration
```

**Structure Decision**: Single project structure with clear layered architecture following DDD principles. Dependencies flow inward: `infrastructure → application → domain`. The domain layer contains pure business logic with no external dependencies. Infrastructure layer handles FastAPI routes, SQLAlchemy persistence, and event publishing. Application layer orchestrates use cases and enforces policies.

## Complexity Tracking

| Pattern/Abstraction | Why Needed | Simpler Alternative Rejected Because |
|---------------------|------------|-------------------------------------|
| Repository pattern | Enables domain layer to be testable without database, allows switching persistence strategies | Direct SQLAlchemy access in domain couples business logic to infrastructure, makes unit testing require database |
| EventPublisher interface | Allows domain/application to emit events without knowing event infrastructure (in-memory, message queue, etc.) | Direct event handling code would couple domain to specific event system, prevent testing in isolation |
