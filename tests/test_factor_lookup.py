import pandas as pd
import pytest

from src.factors import find_factor, load_factors, to_factor_unit
from src.schema import InvoiceData


def sample_factors():
    return pd.DataFrame(
        [
            {"activity_type": "electricity", "energy_or_fuel": "grid_electricity",
             "unit": "kWh", "factor": 0.5, "scope": 2},
            {"activity_type": "fuel", "energy_or_fuel": "diesel",
             "unit": "litre", "factor": 2.0, "scope": 1},
        ]
    )


def electricity_invoice(quantity=2.5, unit="MWh"):
    return InvoiceData(
        invoice_type="electricity",
        period_start="2025-03-01",
        period_end="2025-03-31",
        quantity=quantity,
        unit=unit,
    )


def test_mwh_is_converted_to_kwh():
    quantity, unit = to_factor_unit(2.5, "MWh")
    assert quantity == pytest.approx(2500)
    assert unit == "kWh"


def test_other_units_stay_the_same():
    assert to_factor_unit(100, "litre") == (100, "litre")


def test_finds_electricity_factor_for_mwh_invoice():
    row = find_factor(electricity_invoice(), sample_factors())
    assert row["factor"] == pytest.approx(0.5)


def test_missing_factor_raises():
    invoice = InvoiceData(
        invoice_type="fuel",
        fuel_type="petrol",
        period_start="2025-03-01",
        period_end="2025-03-31",
        quantity=100,
        unit="litre",
    )
    with pytest.raises(ValueError, match="No factor"):
        find_factor(invoice, sample_factors())


def test_duplicate_factor_rows_raise():
    factors = pd.concat([sample_factors(), sample_factors().iloc[[0]]])
    with pytest.raises(ValueError, match="Multiple"):
        find_factor(electricity_invoice(), factors)


def test_every_ground_truth_invoice_has_a_factor():
    truth = pd.read_csv("tests/ground_truth.csv")
    factors = load_factors()
    for _, row in truth.iterrows():
        invoice = InvoiceData(
            invoice_type=row["invoice_type"],
            fuel_type=None if pd.isna(row["fuel_type"]) else row["fuel_type"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            quantity=row["quantity"],
            unit=row["unit"],
        )
        assert find_factor(invoice, factors)["factor"] > 0
