import pytest

from src.extract_rules import FIELDS
from src.hybrid import merge_fields
from src.policy import decide, trusted_total

GOOD = {"invoice_type": "electricity", "quantity": 404.0, "unit": "kWh", "total_amount": 115.3}
ELECTRICITY_TEXT = (
    "Northwind Energy\nDescription: Electricity supply\n"
    "Consumption: 404 kWh\nTotal due: EUR 115.30\n"
)
DIESEL = {
    "invoice_type": "fuel", "fuel_type": "diesel",
    "quantity": 900.0, "unit": "litre", "total_amount": 1570.0,
}


def fields(**values):
    data = {name: None for name in FIELDS}
    data.update(values)
    return data


def merged_from(regex, llm):
    return merge_fields(fields(**regex), fields(**llm))


def test_confirmed_invoice_is_processed():
    decision = decide(merged_from(GOOD, GOOD), ELECTRICITY_TEXT)
    assert decision["status"] == "processed"
    assert decision["reasons"] == []


def test_number_both_readers_share_but_missing_from_the_text_is_reviewed():
    wrong = {**GOOD, "quantity": 40400.0}
    decision = decide(merged_from(wrong, wrong), ELECTRICITY_TEXT)
    assert decision["status"] == "needs_review"
    assert any("quantity" in r and "not found" in r for r in decision["reasons"])


def test_single_source_value_is_accepted_when_the_checks_pass():
    regex = {"invoice_type": "electricity", "total_amount": 115.3}
    decision = decide(merged_from(regex, GOOD), ELECTRICITY_TEXT)
    assert decision["status"] == "processed"


def test_single_source_invented_number_goes_to_review():
    text = "BrightGrid Power\nUsage: 842 KWH\nAmount payable: EUR 210.50\n"
    regex = {"invoice_type": "electricity", "total_amount": 210.5}
    llm = {"invoice_type": "electricity", "quantity": 842000.0, "unit": "kWh", "total_amount": 210.5}
    decision = decide(merged_from(regex, llm), text)
    assert decision["status"] == "needs_review"
    assert any("quantity" in r and "not found" in r for r in decision["reasons"])


def test_conflict_goes_to_review_and_suggests_the_candidate_that_passes():
    text = (
        "BrightGrid Power\nLast year's Usage: 4,100 kWh\n"
        "Consumption: 520 kWh\nTotal due: EUR 111.80\n"
    )
    base = {"invoice_type": "electricity", "unit": "kWh", "total_amount": 111.8}
    decision = decide(merged_from({**base, "quantity": 4100.0}, {**base, "quantity": 520.0}), text)
    assert decision["status"] == "needs_review"
    assert decision["suggestions"] == {"quantity": 520.0}
    assert any("quantity: conflict" in r for r in decision["reasons"])


def test_conflict_without_a_clear_winner_has_no_suggestion():
    text = "Acme\nConsumption: 404 kWh\nOther: 500 kWh\nTotal due: EUR 115.30\n"
    base = {"invoice_type": "electricity", "unit": "kWh", "total_amount": 115.3}
    decision = decide(merged_from({**base, "quantity": 404.0}, {**base, "quantity": 500.0}), text)
    assert decision["status"] == "needs_review"
    assert decision["suggestions"] == {}


def test_confirmed_fuel_product_is_processed():
    text = "Apex Fuels\nDescription: Diesel\nConsumption: 900 litre\nTotal due: EUR 1570.00\n"
    decision = decide(merged_from(DIESEL, DIESEL), text)
    assert decision["status"] == "processed"


def test_unknown_fuel_product_goes_to_review_even_if_readers_agree():
    text = (
        "RoadStar Petrol\nDescription: Gasoil (B7)\n"
        "Consumption: 900 litre\nTotal due: EUR 1570.00\n"
    )
    petrol = {**DIESEL, "fuel_type": "petrol"}
    decision = decide(merged_from(petrol, petrol), text)
    assert decision["status"] == "needs_review"
    assert any("fuel_type" in r for r in decision["reasons"])


def test_unit_must_fit_the_invoice_type():
    text = "Apex Fuels\nDescription: Diesel\nConsumption: 900 kWh\nTotal due: EUR 1570.00\n"
    wrong_unit = {**DIESEL, "unit": "kWh"}
    decision = decide(merged_from(wrong_unit, wrong_unit), text)
    assert decision["status"] == "needs_review"
    assert any(r.startswith("unit") for r in decision["reasons"])


def test_missing_critical_field_goes_to_review():
    partial = {"invoice_type": "electricity", "unit": "kWh"}
    decision = decide(merged_from(partial, partial), ELECTRICITY_TEXT)
    assert decision["status"] == "needs_review"
    assert any(r.startswith("quantity: empty") for r in decision["reasons"])


def test_trusted_total_uses_the_candidate_found_in_the_text():
    merged = merged_from({"total_amount": 1.287}, {"total_amount": 1287.6})
    assert trusted_total(merged, "Total due: EUR 1.287,60") == pytest.approx(1287.6)


def test_total_not_in_the_text_is_not_trusted():
    merged = merged_from({"total_amount": 999.0}, {"total_amount": 999.0})
    assert trusted_total(merged, "Total due: EUR 115.30") is None
