"""
Validator for order data before it's written to the database.

Functions here are pure: they take a dict and return a validation
result. No database or API access — this keeps them easy to test.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """Result of validating a single order."""

    is_valid: bool
    reason: Optional[str] = None  # set when is_valid is False


REQUIRED_FIELDS = ["shopify_order_id", "customer_name", "sku", "quantity", "price"]


def validate_order(order: dict) -> ValidationResult:
    """
    Validate a single order (as a dict).

    Example of a valid order:
        {
            "shopify_order_id": "1001",
            "customer_name": "Jane Doe",
            "sku": "SKU-001",
            "quantity": 2,
            "price": 150000,
        }
    """

    # 1. All required fields must be present and non-empty
    for field in REQUIRED_FIELDS:
        if field not in order or order[field] in (None, ""):
            return ValidationResult(
                is_valid=False,
                reason=f"Required field '{field}' is missing or empty",
            )

    # 2. Quantity must be a positive number
    quantity = order["quantity"]
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        return ValidationResult(
            is_valid=False,
            reason=f"Quantity must be a positive number, got: {quantity!r}",
        )

    # 3. Price must be a positive number
    price = order["price"]
    if not isinstance(price, (int, float)) or price <= 0:
        return ValidationResult(
            is_valid=False,
            reason=f"Price must be a positive number, got: {price!r}",
        )

    # 4. SKU must be non-empty text after stripping whitespace
    sku = order["sku"]
    if not isinstance(sku, str) or not sku.strip():
        return ValidationResult(
            is_valid=False,
            reason=f"SKU must be valid text, got: {sku!r}",
        )

    # All rules passed
    return ValidationResult(is_valid=True)
