# Tasks: Inventory Management REST API

**Input**: Design documents from `/specs/001-inventory-rest-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The specification explicitly requests unit tests with pytest and mocks with unittest.mock. All test tasks are included following TDD approach (tests BEFORE implementation).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths follow plan.md structure with domain/application/infrastructure layers

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create root-level project files (requirements.txt, pytest.ini, Dockerfile)
- [ ] T002 Create src/ directory with __init__.py
- [ ] T003 [P] Create src/domain/ directory with __init__.py
- [ ] T004 [P] Create src/application/ directory with __init__.py
- [ ] T005 [P] Create src/infrastructure/ directory with __init__.py
- [ ] T006 [P] Create tests/unit/ directory
- [ ] T007 [P] Create tests/integration/ directory
- [ ] T008 [P] Create tests/contract/ directory
- [ ] T009 [P] Create src/infrastructure/database/ directory with __init__.py
- [ ] T010 [P] Create src/infrastructure/api/ directory with __init__.py
- [ ] T011 [P] Create src/infrastructure/events/ directory with __init__.py
- [ ] T012 [P] Create src/application/policies/ directory with __init__.py
- [ ] T013 Write requirements.txt with FastAPI, SQLAlchemy, Pydantic, pytest, httpx dependencies
- [ ] T014 Configure pytest.ini with test paths and coverage settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T015 [P] Create domain exceptions in src/domain/exceptions.py (InventoryDomainError, InvalidQuantityError, InsufficientStockError, InventoryNotFoundError)
- [ ] T016 [P] Define domain events in src/domain/events.py (InventoryEvent protocol, InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected)
- [ ] T017 [P] Define domain commands in src/domain/commands.py (ReserveInventory, ReleaseInventory, AdjustInventory)
- [ ] T018 [P] Create EventPublisher interface in src/application/event_publisher.py (abstract base class)
- [ ] T019 [P] Implement LocalEventPublisher in src/infrastructure/events/local_publisher.py (in-memory event publisher)
- [ ] T020 Create SQLAlchemy models in src/infrastructure/database/models.py (InventoryModel with to_domain/from_domain methods, EventLogModel)
- [ ] T021 Create database session management in src/infrastructure/database/session.py (get_db dependency, engine creation)
- [ ] T022 Create repository interface and implementation in src/infrastructure/database/repository.py (InventoryRepository with get, save, find_low_stock methods using SELECT FOR UPDATE)
- [ ] T023 Create Pydantic schemas in src/infrastructure/api/schemas.py (all request/response models from contracts/openapi.yaml)
- [ ] T024 Setup FastAPI app initialization in src/main.py (create app, include routers, CORS middleware, database init)
- [ ] T025 Create dependency injection helpers in src/infrastructure/api/dependencies.py (get_repository, get_event_publisher)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Check Inventory Availability (Priority: P1) 🎯 MVP

**Goal**: Query current inventory status for products

**Independent Test**: Query inventory for a product and verify available quantity calculation is correct

### Tests for User Story 1 (TDD - Write FIRST)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T026 [P] [US1] Write unit test for Inventory aggregate creation with valid data in tests/unit/test_inventory_aggregate.py
- [ ] T027 [P] [US1] Write unit test for Inventory aggregate invariant validation (negative quantities, reserved > total) in tests/unit/test_inventory_aggregate.py
- [ ] T028 [P] [US1] Write unit test for available_quantity property calculation in tests/unit/test_inventory_aggregate.py
- [ ] T029 [P] [US1] Write integration test for querying inventory via service in tests/integration/test_inventory_workflows.py
- [ ] T030 [P] [US1] Write contract test for GET /v1/inventory/{product_id} endpoint in tests/contract/test_inventory_api.py

### Implementation for User Story 1

- [ ] T031 [US1] Implement Inventory aggregate in src/domain/inventory.py (dataclass with product_id, total_quantity, reserved_quantity, minimum_stock_level, available_quantity property, __post_init__ validation)
- [ ] T032 [US1] Implement InventoryService.get_inventory method in src/application/inventory_service.py (retrieve from repository, return inventory status)
- [ ] T033 [US1] Implement GET /v1/inventory/{product_id} endpoint in src/infrastructure/api/routes.py (query service, return InventoryResponse or 404)
- [ ] T034 [US1] Add error handling for InventoryNotFound in src/infrastructure/api/routes.py (convert domain exceptions to HTTP responses)
- [ ] T035 [US1] Run all User Story 1 tests and verify they pass

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reserve Inventory for Orders (Priority: P1)

**Goal**: Reserve inventory atomically to prevent overselling

**Independent Test**: Reserve inventory and verify reserved_quantity increases while available_quantity decreases

### Tests for User Story 2 (TDD - Write FIRST)

- [ ] T036 [P] [US2] Write unit test for Inventory.reserve() success case in tests/unit/test_inventory_aggregate.py
- [ ] T037 [P] [US2] Write unit test for Inventory.reserve() with insufficient stock in tests/unit/test_inventory_aggregate.py
- [ ] T038 [P] [US2] Write unit test for Inventory.reserve() emitting InventoryReserved event in tests/unit/test_inventory_aggregate.py
- [ ] T039 [P] [US2] Write unit test for Inventory.reserve() with negative/zero quantity in tests/unit/test_inventory_aggregate.py
- [ ] T040 [P] [US2] Write integration test for reserve workflow with event emission in tests/integration/test_inventory_workflows.py
- [ ] T041 [P] [US2] Write contract test for POST /v1/inventory/{product_id}/reserve endpoint in tests/contract/test_inventory_api.py

### Implementation for User Story 2

- [ ] T042 [US2] Implement Inventory.reserve(quantity) method in src/domain/inventory.py (validate, update reserved_quantity, return events list)
- [ ] T043 [US2] Implement InventoryService.reserve_inventory method in src/application/inventory_service.py (get with lock, call reserve, save, publish events)
- [ ] T044 [US2] Implement POST /v1/inventory/{product_id}/reserve endpoint in src/infrastructure/api/routes.py (parse request, call service, return OperationResult or errors)
- [ ] T045 [US2] Add error handling for InsufficientStock (409 Conflict) in src/infrastructure/api/routes.py
- [ ] T046 [US2] Implement event publishing in InventoryService for InventoryReserved events
- [ ] T047 [US2] Run all User Story 2 tests and verify they pass

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Release Reserved Inventory (Priority: P2)

**Goal**: Release reserved inventory back to available pool

**Independent Test**: Reserve then release inventory and verify available_quantity returns to original value

### Tests for User Story 3 (TDD - Write FIRST)

- [ ] T048 [P] [US3] Write unit test for Inventory.release() success case in tests/unit/test_inventory_aggregate.py
- [ ] T049 [P] [US3] Write unit test for Inventory.release() with quantity exceeding reserved in tests/unit/test_inventory_aggregate.py
- [ ] T050 [P] [US3] Write unit test for Inventory.release() emitting InventoryReleased event in tests/unit/test_inventory_aggregate.py
- [ ] T051 [P] [US3] Write integration test for release workflow in tests/integration/test_inventory_workflows.py
- [ ] T052 [P] [US3] Write contract test for POST /v1/inventory/{product_id}/release endpoint in tests/contract/test_inventory_api.py

### Implementation for User Story 3

- [ ] T053 [US3] Implement Inventory.release(quantity) method in src/domain/inventory.py (validate against reserved_quantity, update, return events)
- [ ] T054 [US3] Implement InventoryService.release_inventory method in src/application/inventory_service.py (get with lock, call release, save, publish events)
- [ ] T055 [US3] Implement POST /v1/inventory/{product_id}/release endpoint in src/infrastructure/api/routes.py (parse request with reason, call service)
- [ ] T056 [US3] Add error handling for invalid release quantity in src/infrastructure/api/routes.py
- [ ] T057 [US3] Run all User Story 3 tests and verify they pass

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Adjust Inventory Levels (Priority: P2)

**Goal**: Manually adjust inventory for physical stock counts

**Independent Test**: Adjust inventory to new total and verify total_quantity and available_quantity update correctly

### Tests for User Story 4 (TDD - Write FIRST)

- [ ] T058 [P] [US4] Write unit test for Inventory.adjust() increasing total in tests/unit/test_inventory_aggregate.py
- [ ] T059 [P] [US4] Write unit test for Inventory.adjust() decreasing total within limits in tests/unit/test_inventory_aggregate.py
- [ ] T060 [P] [US4] Write unit test for Inventory.adjust() failing when new_total < reserved in tests/unit/test_inventory_aggregate.py
- [ ] T061 [P] [US4] Write unit test for Inventory.adjust() emitting InventoryAdjusted event in tests/unit/test_inventory_aggregate.py
- [ ] T062 [P] [US4] Write integration test for adjustment workflow in tests/integration/test_inventory_workflows.py
- [ ] T063 [P] [US4] Write contract test for PUT /v1/inventory/{product_id} endpoint in tests/contract/test_inventory_api.py

### Implementation for User Story 4

- [ ] T064 [US4] Implement Inventory.adjust(new_total_quantity) method in src/domain/inventory.py (validate invariants, update total, return events)
- [ ] T065 [US4] Implement InventoryService.adjust_inventory method in src/application/inventory_service.py (get with lock, call adjust, save, publish events)
- [ ] T066 [US4] Implement PUT /v1/inventory/{product_id} endpoint in src/infrastructure/api/routes.py (parse AdjustInventoryRequest, call service)
- [ ] T067 [US4] Add error handling for adjustment validation failures in src/infrastructure/api/routes.py
- [ ] T068 [US4] Run all User Story 4 tests and verify they pass

**Checkpoint**: At this point, all core inventory operations (query, reserve, release, adjust) are functional

---

## Phase 7: User Story 5 - Monitor Low Stock Alerts (Priority: P3)

**Goal**: Detect and query products below minimum stock thresholds

**Independent Test**: Reduce product below threshold and verify LowStockDetected event is emitted and low stock query returns it

### Tests for User Story 5 (TDD - Write FIRST)

- [ ] T069 [P] [US5] Write unit test for StockLevelMonitor policy detecting low stock in tests/unit/test_stock_monitor_policy.py
- [ ] T070 [P] [US5] Write unit test for Inventory.reserve() emitting LowStockDetected when below minimum in tests/unit/test_inventory_aggregate.py
- [ ] T071 [P] [US5] Write unit test for Inventory.adjust() emitting LowStockDetected when below minimum in tests/unit/test_inventory_aggregate.py
- [ ] T072 [P] [US5] Write integration test for low stock policy triggering in tests/integration/test_inventory_workflows.py
- [ ] T073 [P] [US5] Write contract test for GET /v1/inventory/low-stock endpoint in tests/contract/test_inventory_api.py

### Implementation for User Story 5

- [ ] T074 [US5] Update Inventory.reserve() to check low stock condition and append LowStockDetected event in src/domain/inventory.py
- [ ] T075 [US5] Update Inventory.adjust() to check low stock condition and append LowStockDetected event in src/domain/inventory.py
- [ ] T076 [US5] Implement StockLevelMonitor policy in src/application/policies/stock_monitor.py (react to events, emit alerts)
- [ ] T077 [US5] Implement InventoryService.get_low_stock_items method in src/application/inventory_service.py (query repository for items below minimum)
- [ ] T078 [US5] Implement repository.find_low_stock() method in src/infrastructure/database/repository.py (SQL query for available < minimum)
- [ ] T079 [US5] Implement GET /v1/inventory/low-stock endpoint in src/infrastructure/api/routes.py (call service, return LowStockResponse)
- [ ] T080 [US5] Run all User Story 5 tests and verify they pass

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T081 [P] Add comprehensive logging to InventoryService in src/application/inventory_service.py (log all operations with product_id and results)
- [ ] T082 [P] Implement event log persistence in EventLogModel saves in src/infrastructure/database/repository.py
- [ ] T083 [P] Add database migration script using Alembic for inventory and event_log tables
- [ ] T084 [P] Create Dockerfile with multi-stage build (builder stage for dependencies, runtime stage for app)
- [ ] T085 [P] Add environment configuration using Pydantic Settings in src/infrastructure/config.py
- [ ] T086 [P] Add health check endpoint GET /health in src/infrastructure/api/routes.py
- [ ] T087 [P] Configure CORS middleware in src/main.py for cross-origin requests
- [ ] T088 [P] Add request ID tracking middleware for debugging in src/infrastructure/api/middleware.py
- [ ] T089 Run full test suite (pytest --cov=src) and verify >90% coverage
- [ ] T090 Validate quickstart.md manual testing scenarios work end-to-end
- [ ] T091 Build Docker image and verify container runs successfully
- [ ] T092 Run performance test for 100 req/sec throughput requirement

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P1): Can start after Foundational - No dependencies on other stories (parallel with US1)
  - User Story 3 (P2): Can start after Foundational - Independent but logically follows US2
  - User Story 4 (P2): Can start after Foundational - Completely independent
  - User Story 5 (P3): Can start after Foundational - May integrate with US2/US4 but independently testable
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Check Inventory)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1 - Reserve Inventory)**: Can start after Foundational (Phase 2) - Parallel with US1, no hard dependency
- **User Story 3 (P2 - Release Inventory)**: Can start after Foundational (Phase 2) - Logically follows reserve but independently testable
- **User Story 4 (P2 - Adjust Inventory)**: Can start after Foundational (Phase 2) - Completely independent of other stories
- **User Story 5 (P3 - Low Stock Alerts)**: Can start after Foundational (Phase 2) - Integrates with reserve/adjust but independently verifiable

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- Domain models before services
- Services before API endpoints
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T003-T012) can run in parallel
- All Foundational tasks marked [P] (T015-T019, T023) can run in parallel within Phase 2
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (both P1)
- All tests within a user story marked [P] can run in parallel
- All domain event/command definitions (T016-T017) can run in parallel
- All Polish tasks marked [P] (T081-T088) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all test tasks for User Story 1 together:
Task T026: Write unit test for Inventory aggregate creation
Task T027: Write unit test for invariant validation
Task T028: Write unit test for available_quantity calculation
Task T029: Write integration test for query workflow
Task T030: Write contract test for GET endpoint

# After tests written and failing, proceed with implementation sequentially:
Task T031: Implement Inventory aggregate (domain model)
Task T032: Implement get_inventory service method
Task T033: Implement GET endpoint
Task T034: Add error handling
Task T035: Run tests (should pass)
```

---

## Parallel Example: User Story 2

```bash
# Launch all test tasks for User Story 2 together:
Task T036: Write unit test for reserve success
Task T037: Write unit test for reserve insufficient stock
Task T038: Write unit test for reserve event emission
Task T039: Write unit test for reserve validation
Task T040: Write integration test
Task T041: Write contract test

# Implementation (sequential within story):
Task T042: Implement Inventory.reserve()
Task T043: Implement InventoryService.reserve_inventory()
Task T044: Implement POST /reserve endpoint
Task T045: Add error handling
Task T046: Implement event publishing
Task T047: Run tests (should pass)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T014)
2. Complete Phase 2: Foundational (T015-T025) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T026-T035)
4. **STOP and VALIDATE**: Test User Story 1 independently with manual scenarios
5. Deploy/demo if ready

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Check Inventory) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Reserve Inventory) → Test independently → Deploy/Demo
4. Add User Story 3 (Release Inventory) → Test independently → Deploy/Demo
5. Add User Story 4 (Adjust Inventory) → Test independently → Deploy/Demo
6. Add User Story 5 (Low Stock Alerts) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Check Inventory)
   - Developer B: User Story 2 (Reserve Inventory)
   - Developer C: User Story 4 (Adjust Inventory)
3. After P1 stories (US1, US2) complete:
   - Developer A: User Story 3 (Release Inventory)
   - Developer B: User Story 5 (Low Stock Alerts)
   - Developer C: Polish tasks
4. Stories complete and integrate independently

---

## TDD Workflow Example

For each user story phase:

1. **RED Phase**: Write failing tests first
   ```bash
   # Example for User Story 1
   pytest tests/unit/test_inventory_aggregate.py::test_create_inventory -v
   # Expected: FAILED (Inventory class not implemented yet)
   ```

2. **GREEN Phase**: Write minimal implementation to pass tests
   ```bash
   # Implement Inventory aggregate in src/domain/inventory.py
   pytest tests/unit/test_inventory_aggregate.py::test_create_inventory -v
   # Expected: PASSED
   ```

3. **REFACTOR Phase**: Improve code while keeping tests green
   ```bash
   # Refactor Inventory implementation
   pytest tests/unit/test_inventory_aggregate.py -v
   # Expected: All PASSED
   ```

4. **Repeat** for each test in the user story

---

## Notes

- [P] tasks = different files, no dependencies (can run in parallel)
- [Story] label maps task to specific user story for traceability (US1, US2, US3, US4, US5)
- Each user story should be independently completable and testable
- Verify tests fail before implementing (RED-GREEN-REFACTOR)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are written FIRST for all user stories (TDD approach as specified)
- Use unittest.mock for external dependencies (EventPublisher, Repository) in unit tests

---

## Task Summary

- **Total Tasks**: 92
- **Setup Phase**: 14 tasks
- **Foundational Phase**: 11 tasks (BLOCKING)
- **User Story 1**: 10 tasks (5 tests + 5 implementation)
- **User Story 2**: 12 tasks (6 tests + 6 implementation)
- **User Story 3**: 10 tasks (5 tests + 5 implementation)
- **User Story 4**: 11 tasks (6 tests + 5 implementation)
- **User Story 5**: 12 tasks (5 tests + 7 implementation)
- **Polish Phase**: 12 tasks

**Parallel Opportunities**: 32 tasks marked with [P] can run concurrently
**MVP Scope** (User Story 1 only): 35 tasks (Setup + Foundational + US1)
**P1 Stories** (US1 + US2): 57 tasks for core functionality
