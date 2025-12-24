# Setting up


## install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

## install spec kit

uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

## claude code

curl -fsSL https://claude.ai/install.sh | bash

claude -> to login

## setup spec kit
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

specify init .


1. spec-kit has created 2 folders:

.specify
.claude

2. claude
runs claude

```bash
claude
```

## Work with spec kit


3. /speckit.constitution We are building a microservice for inventory management. It should be based on Domain Driven Design principles. The Domain Model uses these Elements Aggregate, External System, Read Model, Command, Event, Policy, User. It should have a modular project strucutre. It should use the latest stable version of Fastapi with python 3.12. For the database use sqlite with sqlalchemy as ORM. Write unit tests using pytest as well as mocks with unittest.mock. In the end, the whole application should run in a docker container, so we will need a Dockerfile. 

->   
Constitution Created Successfully

  Version: 1.0.0
  Ratified: 2025-12-24

  Summary

  I've created your project constitution for the Inventory Management Microservice with the following core principles:

  Core Principles Established:

  1. Domain-Driven Design (DDD) - Mandates use of Aggregates, Commands, Events, Policies, Read Models, External Systems, and User entities with clear boundaries
  2. Modular Architecture - Enforces independent testability, explicit interfaces, and inward-flowing dependencies (infrastructure → application → domain)
  3. Test-First Development (NON-NEGOTIABLE) - Requires TDD with Red-Green-Refactor cycle using pytest and unittest.mock
  4. Technology Standards - Locks in Python 3.12, FastAPI (latest stable), SQLite with SQLAlchemy ORM, pytest, and Docker
  5. API Contract Discipline - Requires Pydantic models, input validation, consistent error handling, and versioned breaking changes

  Additional Sections:
  - Code Quality & Testing (detailed test organization: unit/integration/contract)
  - Containerization (Docker requirements with multi-stage builds, non-root user, health checks)
  - Governance (amendment process, compliance checks, semantic versioning)

  Template Synchronization

  Updated:
  - .specify/templates/plan-template.md - Added specific constitution check gates for all 5 core principles

  Verified Compatible:
  - .specify/templates/spec-template.md - User story approach aligns with DDD and modular design
  - .specify/templates/tasks-template.md - Phase-based structure supports TDD and independent testing

  Suggested Commit Message

  docs: establish constitution v1.0.0 for inventory microservice

  - Add DDD principles (Aggregates, Commands, Events, Policies, Read Models)
  - Define modular architecture standards with dependency flow rules
  - Mandate test-first development (TDD) as non-negotiable
  - Lock technology stack: Python 3.12, FastAPI, SQLite, SQLAlchemy, pytest, Docker
  - Establish API contract discipline with Pydantic validation
  - Define code quality, testing, and containerization requirements
  - Update plan-template.md with constitution compliance gates

  All templates are now synchronized and ready for use with the /speckit.plan workflow.


4. Manuelles checken vom constitution.md und plan-template.md

5. Zu detailliert im constitution file: Technisches soll da nicht drin sein. Lass uns lieber eine neue constitution.md file generieren

6. /speckit.constitution We are building a microservice for inventory management. It should be based on Domain Driven Design principles. The Domain Model uses these Elements Aggregate, External System, Read Model, Command, Event, Policy, User.

● Perfect! The constitution has been successfully created and all templates have been synchronized. Let me provide you with a summary:

  Constitution Created Successfully

  Version: 1.0.0
  Ratified: 2025-12-24

  Summary

  I've created a streamlined, principle-focused project constitution for the Inventory Management Microservice that avoids overly prescriptive technical details and focuses on timeless architectural principles.

  Core Principles Established

  I. Domain-Driven Design (DDD)
  - Mandates use of 7 standardized DDD elements: Aggregates, Commands, Events, Policies, Read Models, External Systems, and User entities
  - Each element has clear responsibilities and rules
  - Ensures business logic remains central and aligned with domain expertise

  II. Modular Architecture
  - Enforces independent testability and clear module boundaries
  - Requires inward dependency flow: infrastructure → application → domain
  - Domain layer must never depend on infrastructure or application layers

  III. Test-First Development (NON-NEGOTIABLE)
  - Mandatory Red-Green-Refactor TDD cycle
  - Tests must be written before implementation
  - Coverage required for domain logic, services, and API contracts

  IV. API Contract Discipline
  - Explicit, versioned contracts required before implementation
  - Input validation at system boundaries
  - Auto-generated API documentation from contracts

  V. Simplicity First
  - Complexity must be justified
  - YAGNI principle enforced (You Aren't Gonna Need It)
  - Abstractions and patterns require concrete benefit justification

  Key Design Decisions

  Separation of Concerns: The constitution now clearly distinguishes between:
  - Timeless principles (in constitution.md) - architectural values that don't change
  - Technical decisions (in Technical Context section of plan-template.md) - language, frameworks, tools that may evolve

  This prevents the constitution from becoming outdated when technology choices change.

  Template Synchronization

  Updated:
  - .specify/templates/plan-template.md - Constitution Check section now includes all 5 principles with detailed compliance checkboxes

  Verified Compatible:
  - .specify/templates/spec-template.md - User story approach aligns with DDD and modular design
  - .specify/templates/tasks-template.md - Phase-based structure supports TDD and independent testing

  Suggested Commit Message

  docs: establish constitution v1.0.0 for inventory microservice

  - Define 5 core principles: DDD, Modular Architecture, Test-First, API Contracts, Simplicity
  - Mandate 7 DDD elements: Aggregates, Commands, Events, Policies, Read Models, External Systems, User
  - Enforce inward dependency flow and domain layer independence
  - Require TDD with Red-Green-Refactor cycle (non-negotiable)
  - Separate timeless principles from technical decisions
  - Update plan-template.md with comprehensive constitution compliance checks

  All templates are now synchronized and ready for use with the /speckit.plan and other speckit workflows.

7. /speckit.specify Create a Restapi for this microservice. It should have a modular project strucutre. It should use the latest stable version of Fastapi with python 3.12. For the database use sqlite with sqlalchemy as ORM. Use pydantic models for data modelling. Write unit tests using pytest as well as mocks with unittest.mock. In the end, the whole application should run in a docker container, so we will need a Dockerfile. 

● Feature Specification Created Successfully ✅

  Branch: 001-inventory-rest-api
  Spec File: /workspaces/inventory_mvp/specs/001-inventory-rest-api/spec.md
  Checklist: /workspaces/inventory_mvp/specs/001-inventory-rest-api/checklists/requirements.md

  Summary

  I've created a comprehensive feature specification for the Inventory Management REST API that focuses on business requirements and user needs rather than implementation details.

  Key Features Specified

  5 User Stories (prioritized for independent delivery):

  1. P1 - Check Inventory Availability: Query stock levels before orders
  2. P1 - Reserve Inventory for Orders: Hold stock atomically for pending orders
  3. P2 - Release Reserved Inventory: Free up cancelled order reservations
  4. P2 - Adjust Inventory Levels: Manual corrections for stock reconciliation
  5. P3 - Monitor Low Stock Alerts: Proactive restocking notifications

  Functional Requirements

  - 16 functional requirements covering API endpoints, validation, events, and persistence
  - All requirements aligned with DDD principles from the constitution
  - Commands: ReserveInventory, ReleaseInventory, AdjustInventory
  - Events: InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected
  - Read Models: InventoryStatus, LowStockList

  Success Criteria (Technology-Agnostic)

  - Response time: <100ms for 95% of requests
  - Concurrency: Handle 1000 concurrent requests atomically
  - Throughput: 100 requests/second without degradation
  - Data persistence: Zero data loss on restart
  - Error handling: 100% clear error messages
  - Business invariants: Zero violations enforced

  Validation Results ✅

  All quality checks passed:
  - ✅ No implementation details in specification
  - ✅ No [NEEDS CLARIFICATION] markers
  - ✅ All requirements testable and unambiguous
  - ✅ Success criteria measurable and technology-agnostic
  - ✅ Scope clearly bounded with assumptions and out-of-scope items
  - ✅ User stories independently testable

  What Was Excluded (Correctly)

  The specification intentionally excludes implementation details like:
  - Python 3.12, FastAPI, SQLite, SQLAlchemy, Pydantic (technical stack)
  - pytest, unittest.mock (testing tools)
  - Docker, Dockerfile (deployment)
  - Modular project structure (code organization)

  These will be documented in the plan.md Technical Context section when you run /speckit.plan.

  Ready for Next Phase

  The specification is ready for:
  - /speckit.plan - Create implementation plan with technical context (Python, FastAPI, SQLite, Docker, etc.)
  - /speckit.clarify - Optional if you want to refine requirements further

  The plan phase will incorporate your technical requirements (FastAPI, Python 3.12, SQLite, SQLAlchemy, pytest, Docker) into the Technical Context and Constitution Check sections.

8. Wir merken, dass die DDD prinzipien immer rausgelassen werden und deshalb wir das requirements.md anpassen mussten. Das spec.md

9. Wir merken dass keine technische anforderungen reingenommen wurden obwohl wir diese spezifiziert haben. Das KI modell erkennt, dass diese hier nicht in dieser Phase gehören und packt diese nicht rein.

10. /speckit.plan The project should have a modular project strucutre. It should use the latest stable version of Fastapi with python 3.12. For the database use sqlite with sqlalchemy as ORM. Use pydantic models for data modelling. Write unit tests using pytest as well as mocks with unittest.mock. In the end, the whole application should run in a docker container, so we will need a Dockerfile. 