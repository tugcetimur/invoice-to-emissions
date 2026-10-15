import pandas as pd

from src.schema import InvoiceData


def test_messy_ground_truth_is_valid():
    truth = pd.read_csv("tests/ground_truth_messy.csv")
    assert len(truth) == 13
    assert truth["invoice_id"].is_unique
    for _, row in truth.iterrows():
        InvoiceData(
            invoice_type=row["invoice_type"],
            fuel_type=None if pd.isna(row["fuel_type"]) else row["fuel_type"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            quantity=row["quantity"],
            unit=row["unit"],
        )
