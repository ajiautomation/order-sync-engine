"""
Validator untuk data order sebelum masuk ke database.

Fungsi di sini murni (pure function): terima dict, kembalikan hasil validasi.
Tidak menyentuh database atau API sama sekali — supaya gampang ditest.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """Hasil validasi satu order."""

    is_valid: bool
    reason: Optional[str] = None  # diisi kalau is_valid == False


REQUIRED_FIELDS = ["shopify_order_id", "customer_name", "sku", "quantity", "price"]


def validate_order(order: dict) -> ValidationResult:
    """
    Validasi satu order (dalam bentuk dict).

    Contoh order yang valid:
        {
            "shopify_order_id": "1001",
            "customer_name": "Budi Santoso",
            "sku": "SKU-001",
            "quantity": 2,
            "price": 150000,
        }
    """

    # 1. Cek semua field wajib ada dan tidak kosong
    for field in REQUIRED_FIELDS:
        if field not in order or order[field] in (None, ""):
            return ValidationResult(
                is_valid=False,
                reason=f"Field wajib '{field}' tidak ada atau kosong",
            )

    # 2. Cek quantity harus angka positif
    quantity = order["quantity"]
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        return ValidationResult(
            is_valid=False,
            reason=f"Quantity harus angka positif, dapat: {quantity!r}",
        )

    # 3. Cek price harus angka positif
    price = order["price"]
    if not isinstance(price, (int, float)) or price <= 0:
        return ValidationResult(
            is_valid=False,
            reason=f"Price harus angka positif, dapat: {price!r}",
        )

    # 4. Cek SKU harus teks yang tidak kosong setelah di-strip
    sku = order["sku"]
    if not isinstance(sku, str) or not sku.strip():
        return ValidationResult(
            is_valid=False,
            reason=f"SKU harus berupa teks yang valid, dapat: {sku!r}",
        )

    # Semua aturan lolos
    return ValidationResult(is_valid=True)
