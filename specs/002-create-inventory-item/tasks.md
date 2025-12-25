# Tasks: Create Inventory Item

**Input**: Design documents from `/specs/002-create-inventory-item/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature follows Test-First Development (TDD) per constitution. All tests are written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Single project structure: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure is ready for feature extension

**Note**: This feature extends an existing codebase. Setup tasks verify compatibility rather than create new infrastructure.

- [x] T001 Verify database schema has unique constraint on inventory.product_id column
- [x] T002 [P] Review existing domain exceptions in src/domain/exceptions.py for reuse patterns
- [x] T003 [P] Review existing event publisher pattern in src/infrastructure/events/local_publisher.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add new domain elements that both user stories depend on

**⚠️ CRITICAL**: Both user stories need these domain elements. Complete before any user story work.

- [x] T004 Add InventoryAlreadyExistsError exception to src/domain/exceptions.py
- [x] T005 [P] Add CreateInventory command dataclass to src/domain/commands.py
- [x] T006 [P] Add InventoryCreated event dataclass to src/domain/events.py

**Checkpoint**: Domain vocabulary extended - user story implementation can now begin

---

## Phase 3: User Story 1 - Initialize Product Inventory (Priority: P1) 🎯 MVP

**Goal**: Enable warehouse managers to create new inventory records via POST endpoint, initializing stock tracking for new products

**Independent Test**: Create a new product inventory record via POST /v1/inventory and verify it appears in the system with correct initial values (total_quantity=initial_quantity, reserved_quantity=0, available_quantity=initial_quantity)

**Acceptance Criteria**:
1. Creating inventory for non-existent product succeeds with 201 status
2. Creating inventory for existing product fails with 409 status
3. Created record has reserved_quantity=0 and available_quantity=total_quantity

### Tests for User Story 1 (TDD - Write FIRST)

**⚠️ RED PHASE**: Write these tests FIRST, ensure they FAIL before implementation

- [x] T007 [P] [US1] Write unit test for Inventory.create() factory method in tests/unit/test_inventory_aggregate.py
  - Test successful creation with valid inputs
  - Test creation invariants (reserved_quantity=0, available_quantity=initial_quantity)
  - Test InventoryCreated event emission
  - Test LowStockDetected event when initial_quantity < minimum_stock_level
  - Test InvalidQuantityError for negative quantities
  - Test InvalidQuantityError for empty product_id

- [x] T008 [P] [US1] Write integration test for repository.create() in tests/integration/test_inventory_repository_create.py
  - Test successful persistence of new inventory
  - Test IntegrityError → InventoryAlreadyExistsError mapping for duplicate product_id
  - Test created entity is returned with all fields

- [x] T009 [P] [US1] Write unit test for InventoryService.create_inventory() in tests/unit/application/test_inventory_service_create.py
  - Test successful creation flow (create → persist → publish events)
  - Test event publishing after successful creation
  - Test exception propagation (InvalidQuantityError, InventoryAlreadyExistsError)
  - Mock repository and event publisher

- [x] T010 [P] [US1] Write contract test for POST /v1/inventory in tests/contract/test_create_inventory_api.py
  - Test 201 Created response with valid request
  - Test 409 Conflict response for duplicate product
  - Test 422 Validation Error for invalid inputs
  - Test response body matches OperationResult schema
  - Mock InventoryService

**Checkpoint**: All tests written and FAILING (Red phase complete)

### Implementation for User Story 1 (GREEN PHASE)

**⚠️ GREEN PHASE**: Write minimal code to make tests PASS

- [x] T011 [US1] Implement Inventory.create() factory method in src/domain/inventory.py
  - Validate inputs (non-negative quantities, non-empty product_id)
  - Create Inventory instance with reserved_quantity=0
  - Emit InventoryCreated event
  - Check low stock condition and emit LowStockDetected if needed
  - Return (inventory, events) tuple
  - Run tests: pytest tests/unit/domain/test_inventory.py::test_create* -v

- [x] T012 [US1] Implement Repository.create() method in src/infrastructure/database/repository.py
  - Convert Inventory domain entity to InventoryModel database model
  - Persist to database via session.add() and session.commit()
  - Catch IntegrityError and raise InventoryAlreadyExistsError
  - Refresh and return created domain entity
  - Run tests: pytest tests/integration/test_inventory_repository.py::test_create* -v

- [x] T013 [US1] Implement InventoryService.create_inventory() method in src/application/inventory_service.py
  - Call Inventory.create() factory method
  - Call repository.create() to persist
  - Publish events via event_publisher
  - Return created inventory entity
  - Run tests: pytest tests/unit/application/test_inventory_service.py::test_create* -v

- [x] T014 [US1] Add CreateInventoryRequest schema to src/infrastructure/api/schemas.py
  - product_id: str with Field(min_length=1)
  - initial_quantity: int with Field(ge=0)
  - minimum_stock_level: int with Field(ge=0)
  - Add field_validator for product_id to reject whitespace-only

- [x] T015 [US1] Implement POST /v1/inventory endpoint in src/infrastructure/api/routes.py
  - Route decorator: @router.post("/inventory", status_code=201)
  - Accept CreateInventoryRequest body
  - Call service.create_inventory()
  - Return OperationResult with 201 status
  - Map InventoryAlreadyExistsError → 409 HTTP exception
  - Map InvalidQuantityError → 422 HTTP exception
  - Run tests: pytest tests/contract/test_create_inventory_api.py -v

- [x] T016 [US1] Verify all User Story 1 tests pass: pytest tests/ -k "create" -v

**Checkpoint**: User Story 1 complete - creating inventory works end-to-end. Verify manually with curl:
```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "TEST-001", "initial_quantity": 100, "minimum_stock_level": 10}'
```

### Refactor Phase (OPTIONAL)

- [x] T017 [US1] Refactor if needed while keeping tests green
  - Extract common validation logic if duplicated
  - Improve error messages for clarity
  - Add docstrings to public methods
  - Run full test suite: pytest tests/ -v
  - ✅ Code review complete: No refactoring needed. Code follows clean architecture, has clear error messages, and all public methods have docstrings. Validation logic is appropriately separated between early validation (create method) and invariant enforcement (__post_init__).

---

## Phase 4: User Story 2 - Handle Invalid Creation Requests (Priority: P2)

**Goal**: Provide clear validation feedback when warehouse managers submit invalid creation requests

**Independent Test**: Submit various invalid requests (negative quantities, empty product IDs, whitespace-only IDs) and verify appropriate 422 error responses with clear error messages

**Acceptance Criteria**:
1. Negative initial_quantity rejected with 422 and clear error message
2. Negative minimum_stock_level rejected with 422 and clear error message
3. Empty or whitespace-only product_id rejected with 422 and clear error message

**Note**: Most validation logic implemented in User Story 1. This phase adds comprehensive validation test coverage.

### Tests for User Story 2 (TDD - Write FIRST)

**⚠️ RED PHASE**: Write additional validation tests

- [x] T018 [P] [US2] Add comprehensive validation tests to tests/unit/test_inventory_aggregate.py
  - Test Inventory.create() with zero initial_quantity (should succeed per spec)
  - Test Inventory.create() with zero minimum_stock_level (should succeed)
  - Test Inventory.create() with product_id containing special characters (should succeed)
  - Test Inventory.create() with product_id containing Unicode (should succeed)
  - Test error messages are clear and actionable

- [x] T019 [P] [US2] Add comprehensive validation tests to tests/contract/test_create_inventory_api.py
  - Test 422 response for negative initial_quantity with error message
  - Test 422 response for negative minimum_stock_level with error message
  - Test 422 response for empty string product_id
  - Test 422 response for whitespace-only product_id
  - Test 422 response for missing required fields
  - Verify error response includes field location and validation message

**Checkpoint**: Additional validation tests written - 40 total tests passing

### Implementation for User Story 2 (GREEN PHASE)

- [x] T020 [US2] Enhance validation error messages in src/domain/inventory.py if needed
  - Ensure InvalidQuantityError messages clearly state the constraint
  - Format: "Initial quantity must be non-negative, got: -10"
  - Run tests: pytest tests/unit/domain/test_inventory.py -v

- [x] T021 [US2] Verify Pydantic validation messages in src/infrastructure/api/schemas.py
  - Check Field descriptions are clear
  - Verify custom validator error messages are actionable
  - Test with invalid inputs to see actual error messages
  - Run tests: pytest tests/contract/test_create_inventory_api.py -v

- [x] T022 [US2] Add edge case tests per spec (special characters, Unicode, concurrent creation)
  - Document in tests that these cases are supported/handled
  - Run full test suite: pytest tests/ -v

**Checkpoint**: User Story 2 complete - all validation scenarios tested and working. Verify manually:
```bash
# Test negative quantity
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "TEST", "initial_quantity": -10, "minimum_stock_level": 5}'

# Test empty product_id
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "", "initial_quantity": 100, "minimum_stock_level": 10}'
```

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [x] T023 [P] Add logging statements to InventoryService.create_inventory() in src/application/inventory_service.py
  - Log successful creation: logger.info(f"Created inventory for product {product_id}")
  - Log duplicate attempts: logger.warning(f"Duplicate creation attempt for product {product_id}")
  - Log validation failures: logger.warning(f"Invalid creation request: {error}")

- [x] T024 [P] Add OpenAPI metadata to POST /v1/inventory endpoint in src/infrastructure/api/routes.py
  - Verify FastAPI auto-generates docs with request/response examples
  - Add operation summary and description from contracts/openapi.yaml
  - Add response model examples for 201, 409, 422 responses

- [x] T025 [P] Update API documentation by visiting http://localhost:8000/docs
  - Verify POST /v1/inventory appears in Swagger UI
  - Test endpoint directly from Swagger UI
  - Verify request/response schemas are documented

- [x] T026 Run full test suite with coverage: pytest --cov=src --cov-report=html --cov-report=term
  - Target: >90% coverage for new code
  - Review coverage report: open htmlcov/index.html

- [x] T027 Validate quickstart.md examples work
  - Follow each curl example from specs/002-create-inventory-item/quickstart.md
  - Verify all examples produce expected results
  - Update examples if API behavior differs

- [x] T028 [P] Run performance validation per spec SC-001 (<5 second creation)
  - Create inventory for 10 products and measure time
  - Verify average time is well under 5 seconds
  - Document results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (verification tasks)
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS both user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Creates core functionality
- **User Story 2 (Phase 4)**: Depends on Foundational - Can run in parallel with US1 but US1 covers most validation
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - can start after Foundational
  - Delivers: Working POST endpoint for valid inputs
  - MVP deliverable: This story alone provides core value

- **User Story 2 (P2)**: Independent - can start after Foundational
  - Delivers: Comprehensive validation and error handling
  - Enhancement: Improves user experience but US1 includes basic validation
  - Note: Most validation implemented in US1, this adds comprehensive test coverage

### Within Each User Story

**Test-First Development (TDD) Flow**:
1. **RED**: Write tests first (T007-T010 for US1, T018-T019 for US2)
2. **GREEN**: Implement minimal code to pass tests (T011-T016 for US1, T020-T022 for US2)
3. **REFACTOR**: Improve code while keeping tests green (T017 for US1)

**Layer Dependencies**:
- Domain tests before domain implementation
- Repository tests before repository implementation
- Service tests before service implementation
- Contract tests before API implementation
- Domain → Repository → Service → API (bottom-up)

### Parallel Opportunities

**Within Setup Phase**:
- T002 and T003 can run in parallel (different files)

**Within Foundational Phase**:
- T005 and T006 can run in parallel (different files: commands.py vs events.py)

**Within User Story 1 Tests**:
- T007, T008, T009, T010 can ALL run in parallel (different test files)

**Within User Story 2 Tests**:
- T018 and T019 can run in parallel (different test files)

**Within Polish Phase**:
- T023, T024, T025, T028 can ALL run in parallel (different concerns)

**Between User Stories**:
- After Foundational completes, US1 (Phase 3) and US2 (Phase 4) can be worked on in parallel by different developers
- However, US2 builds on US1's validation, so sequential implementation (US1 → US2) is more efficient

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all User Story 1 test writing tasks together:
Task T007: "Write unit test for Inventory.create() in tests/unit/domain/test_inventory.py"
Task T008: "Write integration test for repository.create() in tests/integration/test_inventory_repository.py"
Task T009: "Write unit test for InventoryService.create_inventory() in tests/unit/application/test_inventory_service.py"
Task T010: "Write contract test for POST /v1/inventory in tests/contract/test_create_inventory_api.py"

# All can be written simultaneously in different files
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Fastest path to working feature**:

1. Complete Phase 1: Setup (verify infrastructure) - ~15 min
2. Complete Phase 2: Foundational (add domain elements) - ~30 min
3. Complete Phase 3: User Story 1 (TDD cycle) - ~3-4 hours
   - Write all tests (RED phase)
   - Implement to pass tests (GREEN phase)
   - Refactor if needed
4. **STOP and VALIDATE**: Test creation endpoint manually
5. **DEPLOY**: MVP ready - warehouse managers can create inventory

**Value Delivered**: Core functionality to create inventory records. Includes basic validation.

### Incremental Delivery

**Full feature with comprehensive validation**:

1. Complete Setup + Foundational → ~45 min
2. Complete User Story 1 → Test independently → Deploy (MVP) → ~4 hours
3. Complete User Story 2 → Test independently → Deploy (Enhanced) → ~2 hours
4. Complete Polish → Final validation → Deploy (Production-ready) → ~1 hour

**Total Estimated Time**: ~8 hours for complete feature with TDD

### Parallel Team Strategy

**If you have 2 developers**:

1. **Together**: Complete Setup + Foundational (~45 min)
2. **Split after Foundational**:
   - Developer A: User Story 1 (core functionality)
   - Developer B: User Story 2 (comprehensive validation tests)
3. **Integration**: Developer B's tests may reveal gaps in Developer A's implementation
4. **Polish together**: Both work on final phase

**Note**: Sequential (US1 → US2) is actually more efficient since US2 builds on US1's validation

---

## Task Summary

**Total Tasks**: 28
- Setup: 3 tasks
- Foundational: 3 tasks (BLOCKS both stories)
- User Story 1: 11 tasks (7 test tasks + 4 implementation tasks)
- User Story 2: 5 tasks (2 test tasks + 3 implementation tasks)
- Polish: 6 tasks

**Tasks by User Story**:
- US1 (P1 - MVP): 11 tasks → Core creation functionality
- US2 (P2 - Enhancement): 5 tasks → Comprehensive validation

**Parallel Opportunities**: 15 tasks marked [P] can run in parallel with others in their phase

**Test Coverage**:
- Domain layer: 2 test files
- Repository layer: 1 test file
- Service layer: 1 test file
- API layer: 1 test file
- Total: 5 test files covering all layers

**MVP Scope**: User Story 1 only (14 tasks: Setup + Foundational + US1)
**Full Feature**: Both user stories (22 tasks: Setup + Foundational + US1 + US2)
**Production Ready**: All phases (28 tasks)

---

## Validation Checklist

Before considering this feature complete:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage target met: `pytest --cov=src --cov-report=term` shows >90% for new code
- [ ] Manual test: Create inventory via POST /v1/inventory succeeds
- [ ] Manual test: Duplicate creation returns 409 Conflict
- [ ] Manual test: Invalid input returns 422 with clear error
- [ ] Manual test: Created inventory queryable via GET /v1/inventory/{product_id}
- [ ] API docs updated: http://localhost:8000/docs shows new endpoint
- [ ] Quickstart examples work: All curl commands from quickstart.md execute successfully
- [ ] Performance validated: Creation completes in <5 seconds (SC-001)
- [ ] Low stock event emitted when initial_quantity < minimum_stock_level

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **TDD mandatory**: Tests written BEFORE implementation per constitution
- **Each user story is independently testable**: Can verify US1 works without US2
- **MVP = User Story 1 only**: Delivers core value, US2 enhances validation
- **Verify tests fail before implementing**: Proves tests actually test the code
- **Commit after each task**: Enables easy rollback if needed
- **Stop at any checkpoint**: Validate story independently before proceeding
