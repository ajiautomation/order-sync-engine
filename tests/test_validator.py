"""
Tests for order_validator.py

Run with: pytest tests/test_validator.py -v
"""

from src.validation.order_validator import validate_order


def make_valid_order(**overrides):
    """Helper: build a valid order, with optional field overrides for testing."""
    order = {
        "shopify_order_id": "1001",
        "customer_name": "Jane Doe",
        "sku": "SKU-001",
        "quantity": 2,
        "price": 150000,
    }
    order.update(overrides)
    return order


def test_valid_order_passes():
    result = validate_order(make_valid_order())
    assert result.is_valid is True
    assert result.reason is None


def test_missing_customer_name_fails():
    order = make_valid_order(customer_name="")
    result = validate_order(order)
    assert result.is_valid is False
    assert "customer_name" in result.reason


def test_missing_field_entirely_fails():
    order = make_valid_order()
    del order["sku"]
    result = validate_order(order)
    assert result.is_valid is False
    assert "sku" in result.reason


def test_negative_price_fails():
    order = make_valid_order(price=-100)
    result = validate_order(order)
    assert result.is_valid is False
    assert "Price" in result.reason


def test_zero_price_fails():
    order = make_valid_order(price=0)
    result = validate_order(order)
    assert result.is_valid is False


def test_negative_quantity_fails():
    order = make_valid_order(quantity=-1)
    result = validate_order(order)
    assert result.is_valid is False
    assert "Quantity" in result.reason


def test_non_numeric_price_fails():
    order = make_valid_order(price="expensive")
    result = validate_order(order)
    assert result.is_valid is False


def test_empty_sku_fails():
    order = make_valid_order(sku="   ")
    result = validate_order(order)
    assert result.is_valid is False
    assert "SKU" in result.reason
