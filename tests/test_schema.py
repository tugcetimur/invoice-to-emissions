import pytest
from pydantic import ValidationError

from src.schema import InvoiceData


def valid(**overrides):
    data = {
        "invoice_type": "electricity",
        "period_start": "2025-03-01",
        "period_end": "2025-03-31",
        "quantity": 1200,
        "unit": "kWh",
    }
    data.update(overrides)
    return InvoiceData(**data)


def test_valid_invoice_passes():
    inv = valid()
    assert inv.quantity == 1200


def test_wrong_unit_for_type_fails():
    with pytest.raises(ValidationError):
        valid(unit="litre")


def test_fuel_needs_fuel_type():
    with pytest.raises(ValidationError):
        valid(invoice_type="fuel", unit="litre")


def test_negative_quantity_fails():
    with pytest.raises(ValidationError):
        valid(quantity=-5)


def test_reversed_dates_fail():
    with pytest.raises(ValidationError):
        valid(period_start="2025-04-01", period_end="2025-03-01")
