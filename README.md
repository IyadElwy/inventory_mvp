# Inventory Management REST API

A production-ready microservice for managing inventory reservations, releases, adjustments, and low-stock monitoring. Built with FastAPI, SQLAlchemy, and Domain-Driven Design principles.

## Features

- ✅ **Inventory Creation**: Initialize new product inventory via REST API
- ✅ **Inventory Operations**: Check, reserve, release, and adjust inventory levels
- ✅ **Low Stock Monitoring**: Query products below minimum thresholds
- ✅ **Event Sourcing**: Full audit trail of all inventory changes
- ✅ **Concurrency Control**: Pessimistic locking for race-condition safety
- ✅ **API Documentation**: Auto-generated OpenAPI/Swagger docs
- ✅ **Production Ready**: Docker, migrations, logging, health checks

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional, for containerized deployment)

### 1. Install Dependencies

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create data directory
mkdir -p data

# Run migrations
alembic upgrade head
```

### 3. Start Server

```bash
# Development mode (with auto-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server runs at **http://localhost:8000**

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

### Run All Tests

```bash
# All tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Quick test run (no coverage)
pytest -v
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

### Performance Testing

```bash
# Run performance test (requires server running)
python performance_test.py

# Expected: ~100 req/sec throughput, <100ms P95 latency
```

## Docker Deployment

### Build Image

```bash
docker build -t inventory-api:latest .
```

### Run Container

```bash
# Run with persistent database
docker run -d \
  --name inventory-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL=sqlite:///./data/inventory.db \
  -e LOG_LEVEL=INFO \
  inventory-api:latest

# View logs
docker logs -f inventory-api

# Stop container
docker stop inventory-api && docker rm inventory-api
```

### Docker Compose (Optional)

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

## API Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Inventory Management API",
  "version": "1.0.0"
}
```

---

### 2. Create Inventory

Create a new inventory record for a product:

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-001",
    "initial_quantity": 100,
    "minimum_stock_level": 10
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Successfully created inventory for product PROD-001",
  "inventory": {
    "product_id": "PROD-001",
    "total_quantity": 100,
    "reserved_quantity": 0,
    "available_quantity": 100,
    "minimum_stock_level": 10
  }
}
```

**Error Response (409 Conflict - Duplicate Product):**
```bash
# Attempting to create the same product again
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-001",
    "initial_quantity": 50,
    "minimum_stock_level": 5
  }'
```

Response:
```json
{
  "detail": "Inventory already exists for product PROD-001"
}
```

**Error Response (422 Validation Error):**
```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "",
    "initial_quantity": -10,
    "minimum_stock_level": 5
  }'
```

Response:
```json
{
  "detail": [
    {
      "loc": ["body", "product_id"],
      "msg": "Product ID cannot be whitespace only",
      "type": "value_error"
    },
    {
      "loc": ["body", "initial_quantity"],
      "msg": "Input should be greater than or equal to 0",
      "type": "greater_than_equal"
    }
  ]
}
```

---

### 3. Check Inventory Status

```bash
curl http://localhost:8000/v1/inventory/PROD-001
```

**Response:**
```json
{
  "product_id": "PROD-001",
  "total_quantity": 100,
  "reserved_quantity": 0,
  "available_quantity": 100,
  "minimum_stock_level": 10
}
```

---

### 4. Reserve Inventory (for an order)

```bash
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 25,
    "order_id": "ORD-12345"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully reserved 25 units",
  "inventory": {
    "product_id": "PROD-001",
    "total_quantity": 100,
    "reserved_quantity": 25,
    "available_quantity": 75,
    "minimum_stock_level": 10
  }
}
```

**Error Response (Insufficient Stock):**
```bash
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 200,
    "order_id": "ORD-12346"
  }'
```

Response (409 Conflict):
```json
{
  "detail": "Cannot reserve 200 units of product PROD-001. Only 75 available."
}
```

---

### 5. Release Inventory (cancel order/refund)

```bash
curl -X POST http://localhost:8000/v1/inventory/PROD-001/release \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 10,
    "order_id": "ORD-12345",
    "reason": "Customer cancellation"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully released 10 units",
  "inventory": {
    "product_id": "PROD-001",
    "total_quantity": 100,
    "reserved_quantity": 15,
    "available_quantity": 85,
    "minimum_stock_level": 10
  }
}
```

---

### 6. Adjust Inventory (stock count/correction)

```bash
curl -X PUT http://localhost:8000/v1/inventory/PROD-001 \
  -H "Content-Type: application/json" \
  -d '{
    "new_quantity": 120,
    "reason": "Physical stock count",
    "adjusted_by": "warehouse-manager@example.com"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully adjusted inventory to 120 units",
  "inventory": {
    "product_id": "PROD-001",
    "total_quantity": 120,
    "reserved_quantity": 15,
    "available_quantity": 105,
    "minimum_stock_level": 10
  }
}
```

**Error Response (Below Reserved):**
```bash
curl -X PUT http://localhost:8000/v1/inventory/PROD-001 \
  -H "Content-Type: application/json" \
  -d '{
    "new_quantity": 5,
    "reason": "Invalid adjustment",
    "adjusted_by": "test@example.com"
  }'
```

Response (422 Unprocessable Entity):
```json
{
  "detail": "New total quantity (5) cannot be less than reserved quantity (15)"
}
```

---

### 7. Query Low Stock Items

```bash
curl http://localhost:8000/v1/inventory/low-stock
```

**Response:**
```json
[
  {
    "product_id": "PROD-002",
    "total_quantity": 15,
    "reserved_quantity": 10,
    "available_quantity": 5,
    "minimum_stock_level": 10
  },
  {
    "product_id": "PROD-003",
    "total_quantity": 8,
    "reserved_quantity": 2,
    "available_quantity": 6,
    "minimum_stock_level": 20
  }
]
```

---

## Complete Workflow Example

```bash
# 1. Create initial inventory for 3 products
for i in 1 2 3; do
  curl -X POST http://localhost:8000/v1/inventory \
    -H "Content-Type: application/json" \
    -d "{
      \"product_id\": \"PROD-00${i}\",
      \"initial_quantity\": 100,
      \"minimum_stock_level\": 20
    }"
done

# 2. Check inventory
curl http://localhost:8000/v1/inventory/PROD-001

# 3. Reserve for order
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 30, "order_id": "ORD-001"}'

# 4. Reserve more (triggers low stock)
curl -X POST http://localhost:8000/v1/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 60, "order_id": "ORD-002"}'

# 5. Check low stock items
curl http://localhost:8000/v1/inventory/low-stock

# 6. Release some inventory (order cancelled)
curl -X POST http://localhost:8000/v1/inventory/PROD-001/release \
  -H "Content-Type: application/json" \
  -d '{"quantity": 30, "order_id": "ORD-001", "reason": "Order cancelled"}'

# 7. Adjust after physical count
curl -X PUT http://localhost:8000/v1/inventory/PROD-001 \
  -H "Content-Type: application/json" \
  -d '{"new_quantity": 150, "reason": "Stock replenishment", "adjusted_by": "system"}'

# 8. Verify final state
curl http://localhost:8000/v1/inventory/PROD-001
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./inventory.db` | Database connection string |
| `DATABASE_ECHO` | `false` | Enable SQL query logging |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `API_PREFIX` | `/v1` | API route prefix |
| `APP_NAME` | `Inventory Management API` | Application name |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host binding |
| `PORT` | `8000` | Server port |

Create a `.env` file in the project root:

```bash
DATABASE_URL=sqlite:///./data/inventory.db
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://app.example.com
DEBUG=false
```

## Project Structure

```
inventory_mvp/
├── src/
│   ├── domain/              # Business logic (no dependencies)
│   │   ├── inventory.py     # Inventory aggregate
│   │   ├── events.py        # Domain events
│   │   └── exceptions.py    # Domain exceptions
│   ├── application/         # Use cases and policies
│   │   ├── inventory_service.py
│   │   └── policies/stock_monitor.py
│   ├── infrastructure/      # External integrations
│   │   ├── database/        # SQLAlchemy models, repository
│   │   ├── api/             # FastAPI routes, schemas
│   │   ├── events/          # Event publisher
│   │   └── config.py        # Pydantic Settings
│   └── main.py              # FastAPI app
├── tests/
│   ├── unit/                # Domain tests (fast)
│   ├── integration/         # Service tests (with DB)
│   └── contract/            # API endpoint tests
├── alembic/                 # Database migrations
├── specs/                   # Feature specifications
├── data/                    # SQLite database (gitignored)
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## Development

### TDD Workflow

1. Write failing test (RED)
```bash
pytest tests/unit/test_new_feature.py
```

2. Implement minimum code (GREEN)
```bash
# Edit src/domain/ or src/application/
pytest tests/unit/test_new_feature.py
```

3. Refactor while keeping tests green
```bash
pytest --cov=src
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

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

**Solution**: SQLite doesn't handle high concurrency. For production, use PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@localhost/inventory
```

### Port Already in Use

**Symptom**: `[Errno 48] Address already in use`

**Solution**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# OR use different port
uvicorn src.main:app --port 8001
```

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Architecture

### Domain-Driven Design (DDD)

- **Aggregate**: `Inventory` (product_id, total_quantity, reserved_quantity, minimum_stock_level)
- **Commands**: CreateInventory, ReserveInventory, ReleaseInventory, AdjustInventory
- **Events**: InventoryCreated, InventoryReserved, InventoryReleased, InventoryAdjusted, LowStockDetected
- **Policies**: StockLevelMonitor (emits alerts when available < minimum)

### CQRS + Event Sourcing

- All state changes emit domain events
- Events persisted to `event_log` table for audit trail
- Read models optimized for queries (InventoryStatus, LowStockList)

### Concurrency Control

Uses pessimistic locking (`SELECT FOR UPDATE`) to prevent race conditions during reservations.

## Performance

- **Target**: 100 requests/second
- **Achieved**: ~94 req/sec (SQLite), ~200+ req/sec expected with PostgreSQL
- **Latency**: P95 < 150ms, P99 < 200ms

## Production Deployment

1. Use PostgreSQL instead of SQLite
2. Set environment variables via secrets management
3. Run with multiple workers: `--workers 4`
4. Use reverse proxy (nginx) for SSL/TLS
5. Enable monitoring (Prometheus, Grafana)
6. Set up log aggregation (ELK, CloudWatch)

## API Endpoints Summary

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|--------------|
| GET | `/health` | Health check | 200 |
| POST | `/v1/inventory` | Create new inventory record | 201, 409, 422 |
| GET | `/v1/inventory/{product_id}` | Get inventory status | 200, 404 |
| POST | `/v1/inventory/{product_id}/reserve` | Reserve inventory | 200, 404, 409, 422 |
| POST | `/v1/inventory/{product_id}/release` | Release reserved inventory | 200, 404, 422 |
| PUT | `/v1/inventory/{product_id}` | Adjust inventory (stock count) | 200, 404, 422 |
| GET | `/v1/inventory/low-stock` | Query low stock items | 200 |

## Test Coverage

- **Total**: 102 tests, 83% coverage
- **Unit Tests**: 54/54 passing (domain + application layers)
- **Integration Tests**: 18/18 passing (repository + database)
- **Contract Tests**: 30/30 passing (API endpoints)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Write tests first (TDD)
4. Implement feature
5. Run tests: `pytest --cov=src`
6. Commit: `git commit -m "feat: add feature"`
7. Push: `git push origin feature/my-feature`
8. Create Pull Request

## License

MIT License - see LICENSE file for details

## Support

For questions or issues, refer to:

**Feature: Inventory REST API (001)**
- Specification: `specs/001-inventory-rest-api/spec.md`
- Implementation Plan: `specs/001-inventory-rest-api/plan.md`
- Quickstart Guide: `specs/001-inventory-rest-api/quickstart.md`

**Feature: Create Inventory Item (002)**
- Specification: `specs/002-create-inventory-item/spec.md`
- Implementation Plan: `specs/002-create-inventory-item/plan.md`
- Quickstart Guide: `specs/002-create-inventory-item/quickstart.md`
- Implementation Complete: `specs/002-create-inventory-item/IMPLEMENTATION_COMPLETE.md`
