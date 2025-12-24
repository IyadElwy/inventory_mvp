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