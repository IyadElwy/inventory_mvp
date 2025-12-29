"""
Domain exceptions for inventory management.
"""


class InventoryDomainError(Exception):
    """Base exception for inventory domain errors"""
    pass


class InvalidQuantityError(InventoryDomainError):
    """Raised when quantity violates business rules"""
    pass


class InsufficientStockError(InventoryDomainError):
    """Raised when reservation exceeds available quantity"""
    pass


class InventoryNotFoundError(InventoryDomainError):
    """Raised when product not found in inventory"""
    pass


class InventoryAlreadyExistsError(InventoryDomainError):
    """Raised when attempting to create inventory for product that already exists"""
    pass
