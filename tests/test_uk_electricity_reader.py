"""v2 regex reader: energy type and billing period.

The rules are in docs/v2-electricity-design.md, "The regex reader". The short texts are invented.
"""

import csv

import pytest

from src.extract_rules import read_pdf_text
from src.uk_electricity import read_energy_type, read_period

JAN = ("2025-01-01", "2025-01-31")


# Period

@pytest.mark.parametrize("text", [
    "Billing period 01 Jan 2025 – 31 Jan 2025",
    "Supply period: 01 Jan 2025 - 31 Jan 2025",
    "Charges for 1 January 2025 to 31 January 2025",
    "Period 01/01/2025 - 31/01/2025",
    "Dates: 2025-01-01 to 2025-01-31",
])
def test_the_one_date_range_is_the_period_whatever_the_label_or_format(text):
    assert read_period(text) == (JAN, None)


def test_the_same_range_printed_twice_is_one_period():
    assert read_period("01 Jan 2025 - 31 Jan 2025\nUsage 01 Jan 2025 - 31 Jan 2025") == (JAN, None)


def test_a_single_date_is_not_a_period():
    assert read_period("Issue date 02 Feb 2025") == (None, "period_not_found")


def test_two_different_ranges_go_to_review():
    text = "01 Jan 2025 - 31 Jan 2025\n01 Feb 2025 - 28 Feb 2025"
    assert read_period(text) == (None, "period_ambiguous")


def test_an_end_before_the_start_goes_to_review():
    assert read_period("31 Jan 2025 - 01 Jan 2025") == (None, "period_invalid")


# Energy type

@pytest.mark.parametrize("text", [
    "Electricity charges",
    "MPAN 12 3456 7890 123",
    "Supply number 12 3456 7890\n123",  # the MPAN core wraps onto the next line
])
def test_an_electricity_marker_gives_electricity(text):
    assert read_energy_type(text) == ("electricity", None)


def test_kwh_alone_is_not_a_marker():
    assert read_energy_type("Used 450 kWh") == (None, "energy_type_unknown")


@pytest.mark.parametrize("text", ["Electricity and gas", "Electricity\nMPRN 1234567", "Electricity 450 m3"])
def test_a_gas_marker_goes_to_review(text):
    assert read_energy_type(text) == (None, "gas_marker_found")


# Dev invoices

with open("tests/ground_truth_uk_electricity_dev.csv", newline="", encoding="utf-8") as f:
    ROWS = list(csv.DictReader(f))


@pytest.mark.parametrize("row", ROWS, ids=[r["invoice_id"] for r in ROWS])
def test_the_dev_invoices_give_the_key_type_and_period(row):
    text = read_pdf_text(f"data/uk_electricity/dev/{row['file_name']}")
    assert read_energy_type(text) == ("electricity", None)
    assert read_period(text) == ((row["period_start"], row["period_end"]), None)
