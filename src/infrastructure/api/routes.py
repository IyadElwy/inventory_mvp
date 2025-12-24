"""
FastAPI route handlers for inventory endpoints.
Handles HTTP request/response and error conversion.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from src.application.inventory_service import InventoryService
from src.infrastructure.api.schemas import InventoryResponse, ErrorResponse
from src.infrastructure.api.dependencies import get_repo_dependency
from src.infrastructure.events.local_publisher import LocalEventPublisher
from src.domain.exceptions import InventoryNotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Inventory"])


def get_inventory_service(repo=Depends(get_repo_dependency)) -> InventoryService:
    """Dependency injection for InventoryService"""
    event_publisher = LocalEventPublisher()
    return InventoryService(repo, event_publisher)


@router.get(
    "/inventory/{product_id}",
    response_model=InventoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
    }
)
def get_inventory(
    product_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Get current inventory status for a product.

    Args:
        product_id: Product identifier

    Returns:
        InventoryResponse with current inventory status

    Raises:
        HTTPException 404: Product not found in inventory
    """
    try:
        logger.info(f"GET /inventory/{product_id}")

        inventory = service.get_inventory(product_id)

        return InventoryResponse(
            product_id=inventory.product_id,
            total_quantity=inventory.total_quantity,
            reserved_quantity=inventory.reserved_quantity,
            available_quantity=inventory.available_quantity,
            minimum_stock_level=inventory.minimum_stock_level
        )

    except InventoryNotFoundError as e:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error getting inventory for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
