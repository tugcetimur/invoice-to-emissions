import pytest

from src.extract_rules import extract_fields, parse_date
from src.schema import InvoiceData

LAYOUT1_ELECTRICITY = """Northwind Energy
Invoice no: INV-2025-001
Description: Electricity supply
Billing period: 01 Mar 2025 - 31 Mar 2025
Consumption: 1,234 kWh
Total due: EUR 345.67
"""

LAYOUT3_GAS = """BlueFlame Gas
Invoice no: INV-2025-007
Description: Natural gas supply
Service dates: 01/03/2025 - 31/03/2025
Previous reading: 45210
Current reading: 45660
Quantity used: 450 m3
Amount excl. VAT: EUR 100.00
VAT 20%: EUR 20.00
Total (incl. VAT): EUR 120.00
"""

LAYOUT2_PETROL = """Apex Fuels
Invoice no: INV-2025-012
Description: Unleaded 95
Statement period: 2025-03-01 - 2025-03-31
Usage: 800 litre
Amount payable: EUR 1500.50
"""


def test_layout1_electricity():
    f = extract_fields(LAYOUT1_ELECTRICITY)
    assert f["supplier"] == "Northwind Energy"
    assert f["invoice_type"] == "electricity"
    assert f["fuel_type"] is None
    assert f["period_start"] == "2025-03-01"
    assert f["period_end"] == "2025-03-31"
    assert f["quantity"] == pytest.approx(1234)
    assert f["unit"] == "kWh"
    assert f["total_amount"] == pytest.approx(345.67)
    assert f["currency"] == "EUR"


def test_layout3_ignores_meter_readings_and_vat():
    f = extract_fields(LAYOUT3_GAS)
    assert f["invoice_type"] == "natural_gas"
    assert f["quantity"] == pytest.approx(450)
    assert f["unit"] == "m3"
    assert f["total_amount"] == pytest.approx(120.00)
    assert f["period_start"] == "2025-03-01"


def test_layout2_petrol_is_recognised():
    f = extract_fields(LAYOUT2_PETROL)
    assert f["invoice_type"] == "fuel"
    assert f["fuel_type"] == "petrol"
    assert f["quantity"] == pytest.approx(800)
    assert f["total_amount"] == pytest.approx(1500.50)


def test_missing_quantity_gives_none():
    f = extract_fields("Some Supplier\nDescription: Electricity supply\n")
    assert f["quantity"] is None
    assert f["unit"] is None


def test_parse_date_formats():
    assert parse_date("01 Mar 2025") == "2025-03-01"
    assert parse_date("2025-03-01") == "2025-03-01"
    assert parse_date("01/03/2025") == "2025-03-01"  # day first assumption
    assert parse_date("not a date") is None


def test_result_fits_the_schema():
    fields = extract_fields(LAYOUT1_ELECTRICITY)
    invoice = InvoiceData(**fields)
    assert invoice.quantity == pytest.approx(1234)
