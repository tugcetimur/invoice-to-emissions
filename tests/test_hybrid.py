from src.extract_rules import FIELDS
from src.hybrid import merge_fields, review_reasons, values_agree

GOOD = {"invoice_type": "electricity", "quantity": 404.0, "unit": "kWh"}


def fields(**values):
    data = {name: None for name in FIELDS}
    data.update(values)
    return data


def test_agreeing_readers_are_confirmed():
    merged = merge_fields(fields(**GOOD), fields(**GOOD))
    assert merged["quantity"]["status"] == "agreed"
    assert merged["quantity"]["value"] == 404.0


def test_numbers_are_compared_with_tolerance():
    assert values_agree("quantity", 404, 404.004)
    assert not values_agree("quantity", 520, 4100)


def test_conflict_keeps_both_candidates_and_no_value():
    merged = merge_fields(fields(quantity=4100.0), fields(quantity=520.0))
    item = merged["quantity"]
    assert item["status"] == "conflict"
    assert item["value"] is None
    assert item["regex"] == 4100.0
    assert item["llm"] == 520.0


def test_single_source_and_empty_statuses():
    merged = merge_fields(fields(unit="kWh"), fields(quantity=500.0))
    assert merged["unit"]["status"] == "regex_only"
    assert merged["quantity"]["status"] == "llm_only"
    assert merged["supplier"]["status"] == "empty"


def test_fully_confirmed_invoice_needs_no_review():
    merged = merge_fields(fields(**GOOD), fields(**GOOD))
    assert review_reasons(merged) == []


def test_single_source_critical_field_needs_review():
    merged = merge_fields(fields(invoice_type="electricity", unit="kWh"), fields(**GOOD))
    assert any("quantity: llm_only" in reason for reason in review_reasons(merged))


def test_conflict_on_critical_field_needs_review():
    merged = merge_fields(fields(**{**GOOD, "quantity": 4100.0}), fields(**GOOD))
    assert any("quantity: conflict" in reason for reason in review_reasons(merged))


def test_conflict_on_non_critical_field_is_ignored():
    merged = merge_fields(
        fields(**GOOD, supplier="INVOICE"), fields(**GOOD, supplier="SunRise Electricity")
    )
    assert review_reasons(merged) == []


def test_fuel_type_is_required_for_fuel_invoices_only():
    fuel = {"invoice_type": "fuel", "quantity": 900.0, "unit": "litre"}
    merged = merge_fields(fields(**fuel), fields(**fuel))
    assert any("fuel_type" in reason for reason in review_reasons(merged))
