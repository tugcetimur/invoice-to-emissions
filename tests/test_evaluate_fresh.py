import pytest

from scripts.evaluate_fresh import classify, truth_emission, values_ok
from src.factors import load_factors


@pytest.mark.parametrize(
    "expected, status, ok, outcome",
    [
        ("process", "processed", True, "correct"),
        ("process", "processed", False, "silent_error"),
        ("review", "processed", True, "silent_error"),
        ("either", "processed", True, "correct"),
        ("either", "processed", False, "silent_error"),
        ("review", "needs_review", False, "needed_review"),
        ("either", "needs_review", False, "acceptable_review"),
        ("process", "needs_review", False, "unneeded_review"),
        ("process", "crash", False, "crash"),
    ],
)
def test_classify_covers_every_combination(expected, status, ok, outcome):
    assert classify(expected, status, ok) == outcome


ROW = {"invoice_type": "electricity", "fuel_type": None, "quantity": 404.0, "unit": "kWh"}


def fields(**overrides):
    return {**ROW, **overrides}


def test_matching_values_are_ok():
    assert values_ok(fields(), ROW)


def test_mwh_and_kwh_are_compared_in_kwh():
    row = {**ROW, "quantity": 1200.0}
    assert values_ok(fields(quantity=1.2, unit="MWh"), row)


def test_a_wrong_quantity_is_not_ok():
    assert not values_ok(fields(quantity=404000.0), ROW)


def test_a_wrong_fuel_type_is_not_ok():
    row = {**ROW, "invoice_type": "fuel", "fuel_type": "diesel", "unit": "litre"}
    assert not values_ok(fields(invoice_type="fuel", fuel_type="petrol", unit="litre"), row)


def test_a_missing_quantity_is_not_ok():
    assert not values_ok(fields(quantity=None), ROW)


TRUTH_ROW = {
    "expected_outcome": "process", "invoice_type": "electricity", "fuel_type": None,
    "period_start": "2025-04-01", "period_end": "2025-04-30", "quantity": 404.0, "unit": "kWh",
}


def test_truth_emission_uses_the_ground_truth_values():
    assert truth_emission(TRUTH_ROW, load_factors()) == pytest.approx(404 * 0.177)


def test_truth_emission_is_zero_when_the_invoice_should_be_reviewed():
    assert truth_emission({**TRUTH_ROW, "expected_outcome": "review"}, load_factors()) == 0.0
