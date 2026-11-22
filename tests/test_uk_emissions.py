"""v2 Scope 2 emissions: location-based and market-based.

The rules are in docs/v2-electricity-design.md, "Location-based and market-based emissions".
The short texts are invented. The LLM is not run here.
"""

import csv

import pytest

from src.extract_rules import read_pdf_text
from src.uk_decision import decide
from src.uk_emissions import market_rule, scope2

FACTOR = 0.177


# Market-based rule

@pytest.mark.parametrize("text", ["Tariff: 100% REGO backed supply", "REGO certificates for 460 kWh"])
def test_rego_with_its_scope_gives_zero(text):
    rule, basis, evidence, reason = market_rule(text, import_kwh=460, export_kwh=0)
    assert (rule, basis, evidence, reason) == ("zero", "REGO", text, None)


def test_rego_without_a_scope_goes_to_review():
    assert market_rule("Supplied with REGOs", 460, 0) == ("review", "unknown", "Supplied with REGOs", "rego_without_scope")


@pytest.mark.parametrize("text", ["REGO for 50% of your supply", "REGO certificates for 300 kWh"])
def test_rego_for_part_of_the_supply_goes_to_review(text):
    assert market_rule(text, 460, 0)[3] == "rego_partial"


@pytest.mark.parametrize("text", ["Green Dynamic Flex 100% Renewable", "Eco tariff", "Solar Electricity", "Zero carbon power"])
def test_a_green_claim_without_rego_goes_to_review(text):
    assert market_rule(text, 460, 0) == ("review", "unknown", text, "green_claim_without_rego")


def test_solar_on_an_invoice_with_export_is_the_customer_panel_not_a_claim():
    assert market_rule("Solar PV Grid Export Credit", 280, 200)[0] == "same"


def test_no_claim_falls_back_to_the_grid_average():
    assert market_rule("Standard Grid Tariff", 460, 0) == ("same", "grid_average_fallback", "", None)


# Emissions

METER = """Period 01 Jan 2025 - 31 Jan 2025
Electricity
Tariff: Standard
METER TYPE PREV CURR USED (KWH) RATE (P) AMOUNT (£)
M1 Actual 12,450 12,910 460 26.50p £121.90
Subtotal £121.90"""


def llm(quantity, start="2025-01-01", end="2025-01-31"):
    return {"invoice_type": "electricity", "quantity": quantity, "unit": "kWh", "period_start": start, "period_end": end}


def test_location_based_is_the_confirmed_kwh_times_the_grid_factor():
    result = scope2(decide(METER, llm(460)), METER)
    assert result["location_kg"] == pytest.approx(460 * FACTOR)
    assert result["market_kg"] == pytest.approx(460 * FACTOR)
    assert (result["factor_value"], result["factor_year"], result["market_basis"]) == (FACTOR, 2025, "grid_average_fallback")
    assert "DESNZ" in result["factor_source"]
    assert result["reasons"] == [] and result["flags"] == []


def test_an_invoice_in_review_gets_no_numbers():
    result = scope2(decide(METER, llm(None) | {"invoice_type": "natural_gas"}), METER)
    assert result["location_kg"] is None and result["market_kg"] is None


def test_market_based_review_writes_no_number_but_keeps_the_location_based():
    text = METER.replace("Tariff: Standard", "Tariff: Green Electricity")
    result = scope2(decide(text, llm(460)), text)
    assert result["location_kg"] == pytest.approx(460 * FACTOR)
    assert result["market_kg"] is None and result["market_rule"] == "review"


def test_a_supplier_emission_claim_is_recorded_and_not_used():
    text = METER + "\nYour tariff saved 84.2 kg CO2 this month"
    result = scope2(decide(text, llm(460)), text)
    assert "supplier_claim_ignored" in result["flags"]
    assert result["location_kg"] == pytest.approx(460 * FACTOR)


def test_a_factor_from_another_year_is_flagged():
    text = METER.replace("2025", "2026")
    result = scope2(decide(text, llm(460, "2026-01-01", "2026-01-31")), text)
    assert "factor_year_differs 2026 vs 2025" in result["flags"]


def test_a_period_across_a_year_boundary_goes_to_review():
    text = METER.replace("01 Jan 2025 - 31 Jan 2025", "15 Dec 2025 - 14 Jan 2026")
    result = scope2(decide(text, llm(460, "2025-12-15", "2026-01-14")), text)
    assert result["reasons"] == ["period_crosses_year"] and result["location_kg"] is None


# Dev invoices

with open("tests/ground_truth_uk_electricity_dev.csv", newline="", encoding="utf-8") as f:
    ROWS = list(csv.DictReader(f))


def dev_text(row):
    return read_pdf_text(f"data/uk_electricity/dev/{row['file_name']}")


@pytest.mark.parametrize("row", ROWS, ids=[r["invoice_id"] for r in ROWS])
def test_the_market_based_rule_matches_the_key(row):
    rule = market_rule(dev_text(row), float(row["import_kwh"]), float(row["export_kwh"]))[0]
    assert rule == row["market_based_rule"]


PROCESSED = [r for r in ROWS if r["expected_outcome"] == "process"]


@pytest.mark.parametrize("row", PROCESSED, ids=[r["invoice_id"] for r in PROCESSED])
def test_the_processed_dev_invoices_give_the_key_emissions(row):
    text = dev_text(row)
    result = scope2(decide(text, llm(float(row["import_kwh"]), row["period_start"], row["period_end"])), text)
    assert result["location_kg"] == pytest.approx(float(row["kg_co2e_location_based"]), abs=0.001)
    if row["kg_co2e_market_based"]:
        assert result["market_kg"] == pytest.approx(float(row["kg_co2e_market_based"]), abs=0.001)
    else:
        assert result["market_kg"] is None
