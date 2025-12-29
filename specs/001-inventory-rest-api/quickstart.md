# Quickstart: Inventory Management API

**Feature**: 001-inventory-rest-api
**Last Updated**: 2025-12-24

## Overview

This guide walks through local development setup, running tests, and deploying the Inventory Management REST API.

## Prerequisites

- Python 3.12 or higher
- Docker (for containerized deployment)
- Git

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd inventory_mvp
git checkout 001-inventory-rest-api
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt** (to be created in implementation):
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
pydantic-settings==2.1.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### 4. Initialize Database

```bash
# Create database directory
mkdir -p data

# Run database migrations (using Alembic)
alembic upgrade head
```

### 5. Run Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server starts at `http://localhost:8000`

### 6. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Suites

```bash
# Unit tests only (fast, no I/O)
pytest tests/unit/ -v

# Integration tests (with database)
pytest tests/integration/ -v

# Contract tests (API endpoints)
pytest tests/contract/ -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term
open htmlcov/index.html  # View coverage report
```

### Test-Driven Development Workflow

1. Write failing test:
   ```bash
   pytest tests/unit/test_inventory_aggregate.py::test_reserve_inventory -v
   # Expected: FAILED (not implemented yet)
   ```

2. Implement minimum code to pass test

3. Run test again:
   ```bash
   pytest tests/unit/test_inventory_aggregate.py::test_reserve_inventory -v
   # Expected: PASSED
   ```

4. Refactor while keeping tests green

## Manual API Testing

### Example: Reserve Inventory

```bash
# 1. Create inventory for a product
curl -X PUT http://localhost:8000/v1/inventory/PROD-001 \
  -H "Content-Type: application/json" \
  -d '{
    "new_quantity": 100,
    "reason": "initial_stock",
    "adjusted_by": "system"
  }'

# 2. Query inventory status
curl http://localhost:8000/v1/inventory/PROD-001

# Expected response:
# {
#   "product_id": "PROD-001",
#   "total_quantity": 100,
#   "reserved_quantity": 0,
#   "available_quantity": 100,
#   "minimum_stock_level": 0
# }

# 3. Reserve inventory
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 20,
    "order_id": "ORD-123"
  }'

# Expected response:
# {
#   "success": true,
#   "message": "Inventory reserved successfully",
#   "inventory": {
#     "product_id": "PROD-001",
#     "total_quantity": 100,
#     "reserved_quantity": 20,
#     "available_quantity": 80,
#     "minimum_stock_level": 0
#   }
# }

# 4. Query low stock items
curl http://localhost:8000/v1/inventory/low-stock
```

### Example: Error Handling

```bash
# Attempt to reserve more than available
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 1000,
    "order_id": "ORD-124"
  }'

# Expected response (409 Conflict):
# {
#   "error": "InsufficientStock",
#   "detail": "Cannot reserve 1000 units. Only 80 available.",
#   "timestamp": "2025-12-24T10:30:00Z"
# }
```

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t inventory-api:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name inventory-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_PATH=/app/data/inventory.db \
  -e LOG_LEVEL=INFO \
  inventory-api:latest
```

### 3. View Logs

```bash
docker logs -f inventory-api
```

### 4. Stop Container

```bash
docker stop inventory-api
docker rm inventory-api
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `./data/inventory.db` | SQLite database file path |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `HOST` | `0.0.0.0` | Server host binding |
| `PORT` | `8000` | Server port |
| `RELOAD` | `false` | Enable auto-reload (dev only) |

## Project Structure

```
inventory_mvp/
├── src/
│   ├── domain/              # Business logic (no external dependencies)
│   │   ├── inventory.py     # Inventory aggregate
│   │   ├── commands.py      # Command definitions
│   │   ├── events.py        # Event definitions
│   │   └── exceptions.py    # Domain exceptions
│   ├── application/         # Use cases and policies
│   │   ├── inventory_service.py
│   │   ├── event_publisher.py
│   │   └── policies/
│   │       └── stock_monitor.py
│   ├── infrastructure/      # External integrations
│   │   ├── database/
│   │   │   ├── models.py    # SQLAlchemy models
│   │   │   ├── repository.py
│   │   │   └── session.py
│   │   ├── api/
│   │   │   ├── routes.py    # FastAPI endpoints
│   │   │   ├── schemas.py   # Pydantic models
│   │   │   └── dependencies.py
│   │   └── events/
│   │       └── local_publisher.py
│   └── main.py              # FastAPI app initialization
├── tests/
│   ├── unit/                # Domain tests (no I/O)
│   ├── integration/         # Service tests (with DB)
│   └── contract/            # API tests
├── data/                    # SQLite database (gitignored)
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## Development Workflow

### Feature Development

1. **Start with failing tests** (TDD):
   ```bash
   pytest tests/unit/test_new_feature.py  # RED
   ```

2. **Implement minimum code**:
   - Add domain logic in `src/domain/`
   - Add service orchestration in `src/application/`
   - Add API endpoint in `src/infrastructure/api/`

3. **Run tests until green**:
   ```bash
   pytest tests/unit/test_new_feature.py  # GREEN
   ```

4. **Refactor**:
   - Improve code quality while keeping tests green

5. **Run full test suite**:
   ```bash
   pytest --cov=src
   ```

6. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature with tests"
   ```

### Code Quality Checks

```bash
# Type checking (if using mypy)
mypy src/

# Linting (if using ruff)
ruff check src/ tests/

# Formatting (if using black)
black src/ tests/
```

## Troubleshooting

### Database Locked Error

**Symptom**: `sqlite3.OperationalError: database is locked`

**Solution**: SQLite doesn't handle high concurrency well. For production, consider PostgreSQL or ensure only one writer at a time.

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure you're running from repo root or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Port Already in Use

**Symptom**: `[Errno 48] Address already in use`

**Solution**: Kill existing process or use different port:
```bash
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
# OR
uvicorn src.main:app --port 8001  # Use different port
```

## Next Steps

1. Run `/speckit.tasks` to generate implementation task list
2. Start with Phase 1: Setup (project structure, dependencies)
3. Move to Phase 2: Foundational (domain models, tests)
4. Implement user stories in priority order (P1 → P2 → P3)
5. Deploy to staging/production environment

## Resources

- **Feature Spec**: [spec.md](spec.md)
- **Implementation Plan**: [plan.md](plan.md)
- **Data Model**: [data-model.md](data-model.md)
- **API Contracts**: [contracts/openapi.yaml](contracts/openapi.yaml)
- **Research**: [research.md](research.md)

## Support

For questions or issues, refer to project documentation in `/specs/001-inventory-rest-api/` or consult the team lead.
