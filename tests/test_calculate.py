import pandas as pd
import pytest

from src.calculate import calculate_emissions
from src.schema import InvoiceData


def sample_factors():
    return pd.DataFrame(
        [
            {"activity_type": "electricity", "energy_or_fuel": "grid_electricity",
             "unit": "kWh", "factor": 0.5, "factor_unit": "kgCO2e/kWh",
             "scope": 2, "source": "Test source", "year": 2025},
            {"activity_type": "fuel", "energy_or_fuel": "diesel",
             "unit": "litre", "factor": 2.0, "factor_unit": "kgCO2e/litre",
             "scope": 1, "source": "Test source", "year": 2025},
        ]
    )


def electricity_invoice(quantity, unit):
    return InvoiceData(
        invoice_type="electricity",
        period_start="2025-03-01",
        period_end="2025-03-31",
        quantity=quantity,
        unit=unit,
    )


def test_electricity_kwh_calculation():
    result = calculate_emissions(electricity_invoice(1000, "kWh"), sample_factors())
    assert result.kg_co2e == pytest.approx(500)
    assert result.t_co2e == pytest.approx(0.5)
    assert result.scope == 2


def test_mwh_gives_same_result_as_kwh():
    from_mwh = calculate_emissions(electricity_invoice(2.5, "MWh"), sample_factors())
    from_kwh = calculate_emissions(electricity_invoice(2500, "kWh"), sample_factors())
    assert from_mwh.kg_co2e == pytest.approx(from_kwh.kg_co2e)
    assert from_mwh.kg_co2e == pytest.approx(1250)


def test_diesel_is_scope_1():
    invoice = InvoiceData(
        invoice_type="fuel",
        fuel_type="diesel",
        period_start="2025-03-01",
        period_end="2025-03-31",
        quantity=100,
        unit="litre",
    )
    result = calculate_emissions(invoice, sample_factors())
    assert result.kg_co2e == pytest.approx(200)
    assert result.scope == 1


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
        calculate_emissions(invoice, sample_factors())


def test_real_electricity_factor_golden_value():
    # 1000 kWh x 0.177 kgCO2e/kWh (UK DESNZ 2025) = 177 kg
    result = calculate_emissions(electricity_invoice(1000, "kWh"))
    assert result.kg_co2e == pytest.approx(177.0)
