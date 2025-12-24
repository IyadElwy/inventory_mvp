"""
Pydantic models for API request/response validation.
These schemas define the API contract and enable automatic validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# Request Schemas

class ReserveInventoryRequest(BaseModel):
    """Request to reserve inventory"""
    quantity: int = Field(..., gt=0, description="Quantity to reserve (must be positive)")
    order_id: str = Field(..., min_length=1, description="Order ID for idempotency")

    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than zero')
        return v


class ReleaseInventoryRequest(BaseModel):
    """Request to release reserved inventory"""
    quantity: int = Field(..., gt=0, description="Quantity to release")
    order_id: str = Field(..., min_length=1, description="Order ID")
    reason: str = Field(..., min_length=1, description="Reason for release")


class AdjustInventoryRequest(BaseModel):
    """Request to adjust inventory"""
    new_quantity: int = Field(..., ge=0, description="New total quantity (must be non-negative)")
    reason: str = Field(..., min_length=1, description="Reason for adjustment")
    adjusted_by: str = Field(..., min_length=1, description="User or system performing adjustment")


# Response Schemas

class InventoryResponse(BaseModel):
    """Response with current inventory status"""
    product_id: str
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    minimum_stock_level: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "PROD-12345",
                "total_quantity": 100,
                "reserved_quantity": 20,
                "available_quantity": 80,
                "minimum_stock_level": 10
            }
        }
    }


class OperationResult(BaseModel):
    """Generic operation result"""
    success: bool
    message: str
    inventory: InventoryResponse


class LowStockItem(BaseModel):
    """Item in low stock list"""
    product_id: str
    available_quantity: int
    minimum_stock_level: int
    shortfall: int  # minimum_stock_level - available_quantity


class LowStockResponse(BaseModel):
    """Response with low stock items"""
    items: list[LowStockItem]
    count: int


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "InsufficientStock",
                "detail": "Cannot reserve 10 units. Only 5 available.",
                "timestamp": "2025-12-24T10:30:00Z"
            }
        }
    }
