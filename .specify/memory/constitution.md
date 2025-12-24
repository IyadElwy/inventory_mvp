<!--
SYNC IMPACT REPORT
==================
Version Change: Initial (none) → 1.0.0
Modified Principles: N/A (initial creation)
Added Sections:
  - Domain-Driven Design Principles
  - Modular Architecture
  - Test-First Development
  - Technology Standards
  - Code Quality & Testing
  - Containerization
Removed Sections: N/A
Templates Requiring Updates:
  ✅ plan-template.md - UPDATED with specific constitution checks for DDD, modular architecture, test-first, tech standards, and API contracts
  ✅ spec-template.md - reviewed, aligns with requirements and user story approach
  ✅ tasks-template.md - reviewed, supports modular implementation and testing discipline
Follow-up TODOs: None
-->

# Inventory Management Microservice Constitution

## Core Principles

### I. Domain-Driven Design (DDD)

The system MUST be built following Domain-Driven Design principles with clear separation of concerns.

**Rules**:
- Aggregates MUST be the consistency boundary for all business logic
- Commands MUST represent user intent and be validated before execution
- Events MUST be immutable records of state changes
- Policies MUST encapsulate business rules and react to events
- Read Models MUST be optimized for query patterns, separate from write models
- External Systems MUST be isolated behind anti-corruption layers
- User entity MUST represent actors in the system with proper authorization context

**Rationale**: DDD ensures business logic remains central, maintainable, and aligned with business requirements. Clear boundaries prevent unintended coupling and enable independent evolution of components.


### Domain Model

#### Aggregate: Inventory
- **Responsibility**: Manages stock levels for products, validates reservations, and enforces stock invariants
- **State**:
  - ProductId (identifier)
  - TotalQuantity (total stock)
  - ReservedQuantity (reserved for orders)
  - AvailableQuantity (calculated: Total - Reserved)
  - MinimumStockLevel (threshold for alerts)
- **Invariants**:
  - AvailableQuantity must never be negative
  - ReservedQuantity ≤ TotalQuantity
  - AvailableQuantity = TotalQuantity - ReservedQuantity

#### Commands
1. **ReserveInventory**: Reserve stock for an order (fails if insufficient available quantity)
2. **ReleaseInventory**: Release reserved stock (e.g., when order is cancelled)
3. **AdjustInventory**: Manual stock correction (e.g., after physical inventory count)

#### Events
1. **InventoryReserved**: Emitted when stock is successfully reserved
2. **InventoryReleased**: Emitted when reservation is released
3. **InventoryAdjusted**: Emitted when stock is manually corrected
4. **LowStockDetected**: Emitted by policy when available quantity falls below minimum threshold

#### Policies
- **StockLevelMonitor**: After any inventory change event, check if AvailableQuantity < MinimumStockLevel and emit LowStockDetected

#### Read Models
1. **InventoryStatusReadModel**: Current stock status per product (for product detail pages)
2. **LowStockListReadModel**: List of products with low stock (for admin dashboard)


### II. Modular Architecture

The codebase MUST follow a modular structure where each domain concept has clear boundaries and responsibilities.

**Rules**:
- Each module MUST be independently testable
- Modules MUST communicate through well-defined interfaces (commands, events, queries)
- Dependencies MUST flow inward (infrastructure → application → domain)
- Cross-module dependencies MUST be explicit and minimized
- Shared concerns (logging, auth, error handling) MUST be extracted into reusable components

**Rationale**: Modularity enables parallel development, easier testing, and reduced cognitive load. Clear boundaries make the system more maintainable and allow teams to work independently.

### III. Test-First Development (NON-NEGOTIABLE)

All features MUST follow Test-Driven Development (TDD) practices.

**Rules**:
- Unit tests MUST be written BEFORE implementation
- Tests MUST fail initially, demonstrating the missing functionality
- Implementation proceeds only after tests are approved by stakeholders
- Red-Green-Refactor cycle is MANDATORY
- Mock external dependencies using unittest.mock
- Test coverage MUST include:
  - Unit tests for domain logic (aggregates, policies, commands)
  - Integration tests for service layers
  - Contract tests for API endpoints
  - Edge cases and error scenarios

**Rationale**: TDD ensures code meets requirements from the start, reduces bugs, enables confident refactoring, and serves as living documentation. Non-negotiable because quality is foundational.

### IV. Technology Standards

The system MUST use the following technology stack consistently.

**Mandatory Stack**:
- **Language**: Python 3.12
- **Framework**: FastAPI (latest stable version)
- **Database**: SQLite with SQLAlchemy ORM
- **Testing**: pytest with unittest.mock
- **Containerization**: Docker

**Rules**:
- All dependencies MUST specify exact versions in requirements files
- FastAPI routers MUST follow RESTful conventions
- SQLAlchemy models MUST use declarative base
- Database migrations MUST be version controlled
- Environment-specific configuration MUST be externalized
- Secrets MUST NOT be committed to version control

**Rationale**: Standardization reduces complexity, improves onboarding, ensures compatibility, and leverages proven tools for microservice development.

### V. API Contract Discipline

All API endpoints MUST have explicit contracts defined before implementation.

**Rules**:
- Request/response schemas MUST be defined using Pydantic models
- All endpoints MUST validate input using FastAPI dependency injection
- Error responses MUST follow consistent structure with HTTP status codes
- OpenAPI documentation MUST be automatically generated and kept up-to-date
- Breaking changes MUST be versioned (e.g., /v1/, /v2/)

**Rationale**: Explicit contracts prevent integration issues, enable parallel frontend/backend development, and provide clear documentation for API consumers.

## Code Quality & Testing

### Testing Requirements

**Unit Tests**:
- MUST test domain logic in isolation
- MUST use mocks for external dependencies (database, external systems)
- MUST verify business rule enforcement
- MUST cover edge cases and error paths

**Integration Tests**:
- MUST verify end-to-end workflows through service layer
- MUST use test database instances
- MUST validate event emission and policy execution
- MUST test cross-aggregate interactions

**Test Organization**:
```
tests/
├── unit/           # Domain logic tests (aggregates, policies)
├── integration/    # Service and API tests
└── contract/       # API contract tests
```

### Code Quality Standards

- Type hints MUST be used for all function signatures
- Docstrings MUST follow Google style for public APIs
- Code MUST pass linting (ruff or pylint)
- Formatting MUST be enforced (black or ruff format)
- Complexity violations MUST be justified in code reviews

## Containerization

The application MUST run in a Docker container for consistent deployment.

**Rules**:
- Dockerfile MUST use multi-stage builds to minimize image size
- Dependencies MUST be installed in isolated layer for caching
- Application MUST run as non-root user
- Health check endpoint MUST be defined
- Environment variables MUST be used for runtime configuration
- Container MUST expose clear logging to stdout/stderr

**Rationale**: Containerization ensures environment consistency, simplifies deployment, and enables scalability through orchestration.

## Governance

### Constitution Authority

This constitution supersedes all other development practices. Any deviation MUST be documented and justified with:
1. Clear explanation of why the principle cannot be followed
2. Risk assessment of the deviation
3. Mitigation strategy
4. Approval from technical lead or team consensus

### Amendment Process

1. Proposed changes MUST be documented with rationale
2. Team review and consensus REQUIRED
3. Update all dependent templates and documentation
4. Version increment according to semantic versioning:
   - **MAJOR**: Breaking changes to core principles
   - **MINOR**: New principles or significant expansions
   - **PATCH**: Clarifications, typo fixes, non-semantic updates

### Compliance

- All pull requests MUST verify alignment with constitution principles
- Code reviews MUST check for principle violations
- Unjustified complexity MUST be rejected
- Regular retrospectives MUST assess constitution effectiveness

### Development Guidance

For runtime development guidance and agent-specific instructions, refer to project documentation and feature specifications in `/specs/` directory.

**Version**: 1.0.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24
