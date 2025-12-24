"""
FastAPI route handlers for inventory endpoints.
Handles HTTP request/response and error conversion.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from src.application.inventory_service import InventoryService
from src.infrastructure.api.schemas import (
    InventoryResponse, ErrorResponse, ReserveInventoryRequest, ReleaseInventoryRequest, OperationResult
)
from src.infrastructure.api.dependencies import get_repo_dependency
from src.infrastructure.events.local_publisher import LocalEventPublisher
from src.domain.exceptions import InventoryNotFoundError, InsufficientStockError, InvalidQuantityError
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


@router.post(
    "/inventory/{product_id}/reserve",
    response_model=OperationResult,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        409: {"model": ErrorResponse, "description": "Insufficient stock"},
        422: {"description": "Validation error"}
    }
)
def reserve_inventory(
    product_id: str,
    request: ReserveInventoryRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Reserve inventory for an order.

    Args:
        product_id: Product identifier
        request: Reservation request with quantity and order_id

    Returns:
        OperationResult with updated inventory status

    Raises:
        HTTPException 404: Product not found
        HTTPException 409: Insufficient stock
        HTTPException 422: Invalid request data
    """
    try:
        logger.info(f"POST /inventory/{product_id}/reserve - quantity: {request.quantity}, order: {request.order_id}")

        inventory = service.reserve_inventory(
            product_id=product_id,
            quantity=request.quantity,
            order_id=request.order_id
        )

        inventory_response = InventoryResponse(
            product_id=inventory.product_id,
            total_quantity=inventory.total_quantity,
            reserved_quantity=inventory.reserved_quantity,
            available_quantity=inventory.available_quantity,
            minimum_stock_level=inventory.minimum_stock_level
        )

        return OperationResult(
            success=True,
            message=f"Successfully reserved {request.quantity} units",
            inventory=inventory_response
        )

    except InventoryNotFoundError as e:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except InsufficientStockError as e:
        logger.warning(f"Insufficient stock for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    except InvalidQuantityError as e:
        logger.warning(f"Invalid quantity for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error reserving inventory for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/inventory/{product_id}/release",
    response_model=OperationResult,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        422: {"description": "Validation error"}
    }
)
def release_inventory(
    product_id: str,
    request: ReleaseInventoryRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Release reserved inventory back to available pool.

    Args:
        product_id: Product identifier
        request: Release request with quantity, order_id, and reason

    Returns:
        OperationResult with updated inventory status

    Raises:
        HTTPException 404: Product not found
        HTTPException 422: Invalid request data or quantity exceeds reserved
    """
    try:
        logger.info(f"POST /inventory/{product_id}/release - quantity: {request.quantity}, order: {request.order_id}")

        inventory = service.release_inventory(
            product_id=product_id,
            quantity=request.quantity,
            order_id=request.order_id,
            reason=request.reason
        )

        inventory_response = InventoryResponse(
            product_id=inventory.product_id,
            total_quantity=inventory.total_quantity,
            reserved_quantity=inventory.reserved_quantity,
            available_quantity=inventory.available_quantity,
            minimum_stock_level=inventory.minimum_stock_level
        )

        return OperationResult(
            success=True,
            message=f"Successfully released {request.quantity} units",
            inventory=inventory_response
        )

    except InventoryNotFoundError as e:
        logger.warning(f"Product not found: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except InvalidQuantityError as e:
        logger.warning(f"Invalid quantity for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error releasing inventory for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
