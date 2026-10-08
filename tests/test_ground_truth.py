import pandas as pd


def test_ground_truth_is_consistent():
    truth = pd.read_csv("tests/ground_truth.csv")
    factors = pd.read_csv("data/emission_factors.csv")

    assert len(truth) == 16
    assert truth["invoice_id"].is_unique

    fuel = truth[truth["invoice_type"] == "fuel"]
    assert fuel["fuel_type"].isin(["diesel", "petrol"]).all()
    assert truth[truth["invoice_type"] != "fuel"]["fuel_type"].isna().all()
    assert set(fuel["fuel_type"]).issubset(set(factors["energy_or_fuel"]))

    gas = truth[truth["invoice_type"] == "natural_gas"]
    gas_units = set(factors.loc[factors["activity_type"] == "natural_gas", "unit"])
    assert set(gas["unit"]).issubset(gas_units)
