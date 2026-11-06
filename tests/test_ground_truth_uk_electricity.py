"""The dev answer key must agree with the dev invoices and with itself.

The key is written by hand. These tests catch typos in the key before any measurement:
the quantities and the amount due must appear in the invoice text, and the emissions must
follow the factor and the market-based rule.
"""

import csv
import re
from pathlib import Path

import pdfplumber
import pytest

DEV_DIR = Path("data/uk_electricity/dev")
KEY = Path("tests/ground_truth_uk_electricity_dev.csv")
FACTOR = 0.177  # kgCO2e/kWh, UK DESNZ 2025 grid electricity

# Quantities that are the sum of several lines and are not printed as one number.
DERIVED_QUANTITY = {"D-04": "210 + 160 kWh", "D-05": "1,450 + 820 kWh"}


def read_key():
    with open(KEY, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pdf_text(name):
    with pdfplumber.open(DEV_DIR / name) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def appears(text, value):
    """Is the number in the text, in one of the usual spellings, as a whole number?"""
    value = float(value)
    spellings = {f"{value:,.0f}", f"{value:,.1f}", f"{value:,.2f}", f"{value:.0f}"} if value == int(value) else {f"{value:,.1f}", f"{value:,.2f}"}
    return any(re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d,]|\.\d)", text) for s in spellings)


ROWS = read_key()
IDS = [row["invoice_id"] for row in ROWS]


def test_the_key_has_one_row_per_dev_invoice():
    in_key = {row["file_name"] for row in ROWS}
    on_disk = {path.name for path in DEV_DIR.glob("*.pdf")}
    assert in_key == on_disk, f"only in key: {in_key - on_disk}, only on disk: {on_disk - in_key}"
    assert len(IDS) == len(set(IDS))


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_the_quantity_and_the_amount_due_appear_in_the_invoice_text(row):
    text = pdf_text(row["file_name"])
    if row["invoice_id"] not in DERIVED_QUANTITY:
        assert appears(text, row["import_kwh"]), f"{row['invoice_id']}: {row['import_kwh']} kWh not found"
    assert appears(text, row["amount_due"]), f"{row['invoice_id']}: amount due {row['amount_due']} not found"


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_the_location_based_emission_follows_the_factor(row):
    assert float(row["kg_co2e_location_based"]) == pytest.approx(float(row["import_kwh"]) * FACTOR, abs=0.001)


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_the_market_based_emission_follows_its_rule(row):
    rule, market = row["market_based_rule"], row["kg_co2e_market_based"]
    if rule == "zero":
        assert float(market) == 0.0
    elif rule == "same":
        assert float(market) == pytest.approx(float(row["kg_co2e_location_based"]), abs=0.001)
    else:
        assert rule == "unknown" and market == ""


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_the_period_and_the_outcome_are_valid(row):
    assert row["period_start"] <= row["period_end"]
    assert row["expected_outcome"] in {"process", "review", "either"}
    assert row["tariff"] in {"standard", "green_rego", "green_claimed", "green_label", "solar_label", "solar_export", "mixed"}
