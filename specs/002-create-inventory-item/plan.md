# Implementation Plan: Create Inventory Item

**Branch**: `002-create-inventory-item` | **Date**: 2025-12-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-create-inventory-item/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a POST endpoint to create new inventory records for products. This enables warehouse managers to initialize inventory tracking for new products with specified initial quantity and minimum stock level. The implementation follows existing REST API patterns and DDD structure, adding a CreateInventory command and InventoryCreated event to the domain model.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.109.0, SQLAlchemy 2.0.25, Pydantic 2.5.3
**Storage**: SQLite (development), SQLAlchemy-compatible SQL database (production)
**Testing**: pytest 7.4.4 with pytest-asyncio, pytest-cov, httpx for API tests
**Target Platform**: Linux server (containerized via Docker)
**Project Type**: Single web service (REST API)
**Performance Goals**: <5 seconds for create operations (per spec SC-001), support existing system throughput
**Constraints**: <200ms p95 for API responses, maintain existing database schema compatibility
**Scale/Scope**: Single inventory service, extends existing 4 endpoints (GET, PUT, POST reserve/release) with 1 new POST endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Domain-Driven Design (DDD) Compliance**:
- [x] Aggregates defined with clear consistency boundaries and invariants - Extends existing Inventory aggregate with create capability
- [x] Commands represent user intent and validation rules are specified - CreateInventory command with product_id, initial_quantity, minimum_stock_level validation
- [x] Events identified as immutable records of state changes - InventoryCreated event will be emitted on successful creation
- [x] Policies identified that react to events and enforce business rules - Reuses existing StockLevelMonitor policy for LowStockDetected
- [x] Read models separated from write models (CQRS) where appropriate - Existing read models (InventoryStatusReadModel, LowStockListReadModel) unchanged
- [x] External systems isolated behind anti-corruption layers - N/A for this feature (no external systems)
- [x] User entity represents actors with authorization context - Authorization handled by calling system (documented in spec assumptions)

**II. Modular Architecture Compliance**:
- [x] Module boundaries are clear and independently testable - Follows existing src/domain, src/application, src/infrastructure structure
- [x] Dependencies flow inward (infrastructure → application → domain) - API routes → InventoryService → Inventory aggregate
- [x] Domain layer does NOT depend on infrastructure or application layers - Domain logic in Inventory.create() method, no infrastructure imports
- [x] Cross-module communication uses explicit interfaces (commands/events/queries) - Uses CreateInventory command and InventoryCreated event
- [x] Cross-module dependencies are justified and documented - No new cross-module dependencies introduced

**III. Test-First Development Compliance**:
- [x] Test strategy defined (unit, integration, contract tests) - Unit tests for domain, integration tests for service, contract tests for API
- [x] Tests will be written BEFORE implementation (Red-Green-Refactor) - TDD workflow: test domain logic → test service → test API endpoint
- [x] Mock/stub strategy for external dependencies documented - Mock repository in service tests, mock service in API tests
- [x] Test coverage includes domain logic, service layers, and API contracts - All three layers tested per existing pattern

**IV. API Contract Discipline Compliance**:
- [x] Request/response schemas explicitly defined and validated - CreateInventoryRequest schema with Pydantic validation
- [x] Input validation strategy at system boundaries documented - Pydantic validators for non-negative quantities, non-empty product_id
- [x] Error response structures and HTTP status codes defined - 201 Created, 409 Conflict (duplicate), 422 Validation Error
- [x] API versioning strategy for breaking changes specified - Maintains /v1 prefix, no breaking changes to existing endpoints
- [x] API documentation will be auto-generated from contracts - FastAPI auto-generates OpenAPI docs from Pydantic schemas

**V. Simplicity First Compliance**:
- [x] Solution is the simplest approach that meets requirements - Extends existing patterns (command/event/aggregate), no new frameworks
- [x] All abstractions and patterns are justified with concrete benefits - Reuses proven DDD structure, consistent with existing endpoints
- [x] New dependencies are necessary and evaluated for maintenance burden - Zero new dependencies required
- [x] Any deviations from standards are documented with rationale in Complexity Tracking - No deviations, follows established patterns

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
├── domain/                  # Domain layer (business logic)
│   ├── inventory.py        # Inventory aggregate (ADD create() method)
│   ├── commands.py         # ADD CreateInventory command
│   ├── events.py           # ADD InventoryCreated event
│   └── exceptions.py       # Existing exceptions (reuse)
├── application/            # Application layer (orchestration)
│   ├── inventory_service.py # ADD create_inventory() method
│   └── policies/
│       └── stock_monitor.py # Existing policy (reuse for low stock)
└── infrastructure/         # Infrastructure layer (technical concerns)
    ├── api/
    │   ├── routes.py       # ADD POST /v1/inventory endpoint
    │   └── schemas.py      # ADD CreateInventoryRequest schema
    └── database/
        ├── repository.py   # ADD create() method
        └── models.py       # Existing SQLAlchemy models (reuse)

tests/
├── unit/
│   ├── domain/
│   │   └── test_inventory.py  # ADD tests for Inventory.create()
│   └── application/
│       └── test_inventory_service.py # ADD tests for create_inventory()
├── integration/
│   └── test_inventory_repository.py # ADD tests for repository.create()
└── contract/
    └── test_create_inventory_api.py # ADD API contract tests
```

**Structure Decision**: This feature extends the existing single-project structure following clean architecture layers (domain → application → infrastructure). All new code integrates into established modules without introducing new top-level directories or dependencies.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations. All checks passed without requiring deviations or justifications.

## Post-Phase 1 Constitution Re-Check

*Gate: Verify design artifacts maintain constitutional compliance*

**Status**: ✅ **ALL CHECKS PASSED**

**Verification Summary**:

1. **DDD Compliance Verified**:
   - ✅ data-model.md defines CreateInventory command and InventoryCreated event
   - ✅ Inventory aggregate extended with create() factory method maintaining invariants
   - ✅ StockLevelMonitor policy reused for LowStockDetected events
   - ✅ CQRS pattern maintained (write via commands, read via existing models)

2. **Modular Architecture Verified**:
   - ✅ Project structure shows clean layering (domain → application → infrastructure)
   - ✅ No infrastructure concerns leak into domain layer (Inventory.create() is pure business logic)
   - ✅ Repository pattern isolates database access
   - ✅ All new code extends existing modules without architectural changes

3. **Test-First Development Verified**:
   - ✅ Test structure documented in plan.md (unit, integration, contract layers)
   - ✅ TDD workflow specified: write tests → make them pass → refactor
   - ✅ Mock strategy defined (mock repo in service tests, mock service in API tests)

4. **API Contract Discipline Verified**:
   - ✅ contracts/openapi.yaml provides complete OpenAPI 3.0 specification
   - ✅ Request schema (CreateInventoryRequest) with Pydantic validation defined
   - ✅ Response schemas (201, 409, 422, 500) documented with examples
   - ✅ Maintains /v1 API version prefix, no breaking changes

5. **Simplicity First Verified**:
   - ✅ Zero new dependencies introduced (confirmed in research.md)
   - ✅ Reuses all existing patterns (DDD elements, REST conventions, error handling)
   - ✅ Minimal complexity: 1 command, 1 event, 1 factory method, 1 API endpoint
   - ✅ No unnecessary abstractions or premature optimization

**Conclusion**: Design is ready for implementation via `/speckit.tasks` command.

## Phase Completion Status

- [x] **Phase 0: Research** - Complete ([research.md](research.md))
  - Technical decisions documented
  - Best practices identified
  - Integration patterns confirmed
  - All unknowns resolved

- [x] **Phase 1: Design & Contracts** - Complete
  - [x] Data model defined ([data-model.md](data-model.md))
  - [x] API contracts specified ([contracts/openapi.yaml](contracts/openapi.yaml))
  - [x] Quickstart guide created ([quickstart.md](quickstart.md))
  - [x] Agent context updated (CLAUDE.md)
  - [x] Constitution compliance verified

- [ ] **Phase 2: Task Breakdown** - Pending
  - Run `/speckit.tasks` to generate tasks.md
  - Tasks will follow TDD workflow documented in this plan
