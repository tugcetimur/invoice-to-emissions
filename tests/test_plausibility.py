import pytest

from src.validate import price_is_plausible, price_per_unit


def test_price_per_unit():
    assert price_per_unit(210.5, 842) == pytest.approx(0.25)


def test_missing_values_give_no_price():
    assert price_per_unit(None, 842) is None
    assert price_per_unit(210.5, None) is None
    assert price_per_unit(210.5, 0) is None


def test_normal_electricity_price_is_plausible():
    assert price_is_plausible("electricity", "kWh", 842, 210.5) is True


def test_thousand_times_too_much_quantity_is_not_plausible():
    assert price_is_plausible("electricity", "kWh", 842000, 210.5) is False


def test_mwh_prices_use_their_own_band():
    assert price_is_plausible("electricity", "MWh", 2.5, 625.0) is True
    assert price_is_plausible("electricity", "MWh", 2500, 625.0) is False


def test_fuel_and_gas_prices():
    assert price_is_plausible("fuel", "litre", 900, 1570.0) is True
    assert price_is_plausible("natural_gas", "m3", 312, 245.8) is True


def test_unknown_combination_cannot_be_judged():
    assert price_is_plausible("fuel", "kWh", 100, 150.0) is None
    assert price_is_plausible("electricity", "kWh", 100, None) is None
