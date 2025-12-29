# Quickstart: Create Inventory Item

**Feature**: 002-create-inventory-item
**Date**: 2025-12-25

## What This Feature Does

Adds a POST endpoint to create new inventory records for products. Before this feature, you could only adjust, reserve, or release inventory for products that already existed. Now you can initialize inventory tracking for new products.

## Quick Example

**Create inventory for a new product:**

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-12345",
    "initial_quantity": 100,
    "minimum_stock_level": 10
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Successfully created inventory for product PROD-12345",
  "inventory": {
    "product_id": "PROD-12345",
    "total_quantity": 100,
    "reserved_quantity": 0,
    "available_quantity": 100,
    "minimum_stock_level": 10
  }
}
```

## Development Workflow

### 1. Run Tests

```bash
# Run all tests for this feature
pytest tests/unit/domain/test_inventory.py::test_create -v
pytest tests/unit/application/test_inventory_service.py::test_create -v
pytest tests/integration/test_inventory_repository.py::test_create -v
pytest tests/contract/test_create_inventory_api.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### 2. Start Development Server

```bash
# From repository root
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the Endpoint

**Using curl:**

```bash
# Create inventory
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-NEW-001",
    "initial_quantity": 50,
    "minimum_stock_level": 5
  }'

# Verify it was created
curl http://localhost:8000/v1/inventory/PROD-NEW-001
```

**Using Python httpx:**

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Create inventory
response = client.post(
    "/v1/inventory",
    json={
        "product_id": "PROD-TEST-123",
        "initial_quantity": 100,
        "minimum_stock_level": 10
    }
)

print(response.status_code)  # 201
print(response.json())

# Verify creation
verify = client.get("/v1/inventory/PROD-TEST-123")
print(verify.json())
```

### 4. View API Documentation

FastAPI auto-generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Look for the new `POST /v1/inventory` endpoint under the "Inventory" tag.

## Common Use Cases

### Case 1: Create Inventory with Sufficient Stock

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "WIDGET-500",
    "initial_quantity": 1000,
    "minimum_stock_level": 50
  }'
```

**Result**: Inventory created, no low stock alert.

### Case 2: Create Inventory with Zero Stock

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "OUT-OF-STOCK-ITEM",
    "initial_quantity": 0,
    "minimum_stock_level": 10
  }'
```

**Result**: Inventory created with zero quantity. Low stock event emitted immediately.

### Case 3: Create Inventory Below Minimum Threshold

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "LOW-STOCK-ITEM",
    "initial_quantity": 3,
    "minimum_stock_level": 20
  }'
```

**Result**: Inventory created successfully. Low stock event emitted because 3 < 20.

### Case 4: Attempt to Create Duplicate (Error)

```bash
# First creation succeeds
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD-DUP", "initial_quantity": 100, "minimum_stock_level": 10}'

# Second creation fails with 409
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD-DUP", "initial_quantity": 200, "minimum_stock_level": 20}'
```

**Response (409 Conflict):**
```json
{
  "error": "InventoryAlreadyExists",
  "detail": "Inventory record already exists for product PROD-DUP",
  "timestamp": "2025-12-25T10:30:00Z"
}
```

### Case 5: Invalid Input (Negative Quantity)

```bash
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-INVALID",
    "initial_quantity": -10,
    "minimum_stock_level": 5
  }'
```

**Response (422 Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "initial_quantity"],
      "msg": "Input should be greater than or equal to 0",
      "type": "greater_than_equal"
    }
  ]
}
```

## Integration with Existing Endpoints

After creating inventory, you can use existing endpoints:

```bash
# 1. Create inventory
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD-ABC", "initial_quantity": 100, "minimum_stock_level": 10}'

# 2. Query current status
curl http://localhost:8000/v1/inventory/PROD-ABC

# 3. Reserve some quantity
curl -X POST http://localhost:8000/v1/inventory/PROD-ABC/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 20, "order_id": "ORDER-001"}'

# 4. Adjust total quantity (e.g., after stock count)
curl -X PUT http://localhost:8000/v1/inventory/PROD-ABC \
  -H "Content-Type: application/json" \
  -d '{"new_quantity": 150, "reason": "Stock replenishment", "adjusted_by": "warehouse-user"}'

# 5. Check low stock items
curl http://localhost:8000/v1/inventory/low-stock
```

## Event Monitoring

When inventory is created, the following events may be emitted:

1. **InventoryCreated** (always):
   ```python
   {
       "product_id": "PROD-12345",
       "initial_quantity": 100,
       "minimum_stock_level": 10,
       "timestamp": "2025-12-25T10:30:00Z"
   }
   ```

2. **LowStockDetected** (if initial_quantity < minimum_stock_level):
   ```python
   {
       "product_id": "PROD-12345",
       "available_quantity": 5,
       "minimum_stock_level": 10,
       "timestamp": "2025-12-25T10:30:00Z"
   }
   ```

To view emitted events (if event persistence is enabled):

```bash
# Query event store (implementation-specific)
# Example: SELECT * FROM events WHERE product_id = 'PROD-12345' ORDER BY timestamp DESC
```

## Troubleshooting

### Issue: 409 Conflict on First Creation

**Symptom**: Getting "Inventory already exists" error for a new product.

**Cause**: Product already has an inventory record (possibly created previously).

**Solution**: Use GET to check existing inventory, or use PUT to adjust if you want to update.

```bash
# Check if it exists
curl http://localhost:8000/v1/inventory/PROD-XYZ

# If exists, use PUT to adjust instead
curl -X PUT http://localhost:8000/v1/inventory/PROD-XYZ \
  -H "Content-Type: application/json" \
  -d '{"new_quantity": 100, "reason": "Recount", "adjusted_by": "system"}'
```

### Issue: 422 Validation Error

**Symptom**: Request rejected with validation error.

**Cause**: Invalid input data (negative quantity, empty product_id, etc.).

**Solution**: Check request body matches schema:
- `product_id`: non-empty string
- `initial_quantity`: >= 0
- `minimum_stock_level`: >= 0

```bash
# Correct format
curl -X POST http://localhost:8000/v1/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "VALID-PROD-ID",
    "initial_quantity": 0,
    "minimum_stock_level": 0
  }'
```

### Issue: Database Lock Errors

**Symptom**: Concurrent creation requests causing deadlocks or timeout errors.

**Cause**: High concurrency for same product_id.

**Solution**: This is expected behavior. The database UNIQUE constraint prevents duplicates. One request succeeds (201), others fail (409). Implement retry logic with exponential backoff if needed.

## Database Verification

To verify inventory was created in the database:

```sql
-- SQLite example
SELECT * FROM inventory WHERE product_id = 'PROD-12345';

-- Expected result:
-- product_id      | total_quantity | reserved_quantity | minimum_stock_level
-- PROD-12345      | 100            | 0                 | 10
```

## Next Steps

1. **Integrate with Product Catalog**: When new products are added to your catalog, automatically create inventory records.

2. **Bulk Import**: Extend with batch creation endpoint for bulk imports (currently out of scope).

3. **Event Consumers**: Build integrations that react to InventoryCreated events (notifications, analytics, etc.).

4. **Monitoring**: Set up alerts for LowStockDetected events emitted immediately after creation.

## Contract Reference

Full OpenAPI specification: [contracts/openapi.yaml](contracts/openapi.yaml)

## Support

- API Documentation: http://localhost:8000/docs
- Feature Spec: [spec.md](spec.md)
- Data Model: [data-model.md](data-model.md)
- Implementation Plan: [plan.md](plan.md)
