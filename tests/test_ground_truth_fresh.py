from pathlib import Path

import pandas as pd

from src.schema import InvoiceData

TRUTH = pd.read_csv("tests/ground_truth_fresh.csv")


def test_fresh_set_has_25_invoices_with_unique_ids():
    assert len(TRUTH) == 25
    assert TRUTH["invoice_id"].is_unique


def test_every_invoice_has_an_ideal_outcome():
    assert set(TRUTH["expected_outcome"]) <= {"process", "review", "either"}


def test_process_and_either_rows_are_valid_invoices():
    rows = TRUTH[TRUTH["expected_outcome"].isin(["process", "either"])]
    for _, row in rows.iterrows():
        fuel_type = None if pd.isna(row["fuel_type"]) else row["fuel_type"]
        InvoiceData(
            invoice_type=row["invoice_type"],
            fuel_type=fuel_type,
            period_start=row["period_start"],
            period_end=row["period_end"],
            quantity=row["quantity"],
            unit=row["unit"],
        )


def test_the_duplicate_repeats_the_first_invoice():
    first = TRUTH[TRUTH["invoice_id"] == "F-01"].iloc[0]
    copy = TRUTH[TRUTH["invoice_id"] == "F-20"].iloc[0]
    for column in ["invoice_type", "supplier", "period_start", "period_end", "quantity", "unit", "total_amount"]:
        assert first[column] == copy[column]


def test_every_invoice_has_a_pdf():
    for name in TRUTH["file_name"]:
        assert (Path("data/fresh_invoices") / name).exists()
