import argparse
from pathlib import Path

import pandas as pd

from src.calculate import calculate_emissions
from src.factors import load_factors, to_factor_unit
from src.pipeline import mark_duplicates, process_pdf
from src.schema import InvoiceData


def none_if_nan(value):
    return None if pd.isna(value) else value


def classify(expected, status, ok):
    """What happened to one invoice, judged against its ideal outcome."""
    if status == "crash":
        return "crash"
    if status == "processed":
        if expected == "review":
            return "silent_error"
        return "correct" if ok else "silent_error"
    if expected == "review":
        return "needed_review"
    if expected == "either":
        return "acceptable_review"
    return "unneeded_review"


def values_ok(fields, row):
    """Are the critical values right? Quantities are compared in the factor table's unit."""
    if fields["invoice_type"] != row["invoice_type"]:
        return False
    if row["invoice_type"] == "fuel" and fields["fuel_type"] != none_if_nan(row["fuel_type"]):
        return False
    if fields["quantity"] is None or fields["unit"] is None:
        return False
    got_quantity, got_unit = to_factor_unit(fields["quantity"], fields["unit"])
    want_quantity, want_unit = to_factor_unit(row["quantity"], row["unit"])
    return got_unit == want_unit and abs(got_quantity - want_quantity) < 0.01


def truth_emission(row, factors):
    """Emission (kg) of the ground truth values; 0 if the invoice should not be processed."""
    if row["expected_outcome"] == "review":
        return 0.0
    invoice = InvoiceData(
        invoice_type=row["invoice_type"],
        fuel_type=none_if_nan(row["fuel_type"]),
        period_start=row["period_start"],
        period_end=row["period_end"],
        quantity=row["quantity"],
        unit=row["unit"],
    )
    return calculate_emissions(invoice, factors).kg_co2e


def run_one(pdf_path, factors):
    """Run the pipeline on one invoice; a crash is a result, not a reason to stop."""
    try:
        return process_pdf(pdf_path, factors=factors)
    except Exception as error:
        return {
            "file": pdf_path.name,
            "status": "crash",
            "reasons": [f"{type(error).__name__}: {error}"],
            "suggestions": {},
            "fields": None,
            "candidates": None,
            "emission": None,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", default="tests/ground_truth_fresh.csv")
    parser.add_argument("--pdf-dir", default="data/fresh_invoices")
    args = parser.parse_args()

    truth = pd.read_csv(args.truth)
    factors = load_factors()
    pdf_dir = Path(args.pdf_dir)
    results = mark_duplicates([run_one(pdf_dir / name, factors) for name in truth["file_name"]])

    counts = {}
    silent = []
    system_kg = processed_truth_kg = ideal_kg_total = 0.0

    for (_, row), result in zip(truth.iterrows(), results):
        expected = row["expected_outcome"]
        ideal_kg = truth_emission(row, factors)
        ideal_kg_total += ideal_kg
        ok = (
            result["status"] == "processed"
            and expected != "review"
            and values_ok(result["fields"], row)
        )
        outcome = classify(expected, result["status"], ok)
        counts[outcome] = counts.get(outcome, 0) + 1
        if result["status"] == "processed":
            system_kg += result["emission"]["kg_co2e"]
            processed_truth_kg += ideal_kg

        print(f"{row['invoice_id']}  ideal={expected:8s} {result['status']:13s} {outcome}")
        if outcome == "silent_error":
            silent.append(row["invoice_id"])
            fields = result["fields"]
            print(f"       got   {fields['invoice_type']} {fields['fuel_type']} {fields['quantity']} {fields['unit']}")
            print(
                f"       truth {row['invoice_type']} {none_if_nan(row['fuel_type'])} "
                f"{none_if_nan(row['quantity'])} {none_if_nan(row['unit'])}"
            )
        elif result["reasons"]:
            print(f"       {result['reasons'][0][:110]}")

    total = len(truth)
    processed = sum(1 for r in results if r["status"] == "processed")
    print("\nOutcomes:")
    for name in ("correct", "silent_error", "needed_review", "acceptable_review", "unneeded_review", "crash"):
        print(f"  {name:18s} {counts.get(name, 0)}")
    print(f"\nProcessed automatically: {processed}/{total}")
    print(f"Silent errors: {len(silent)} {silent}")
    if processed_truth_kg > 0:
        deviation = (system_kg - processed_truth_kg) / processed_truth_kg * 100
        print(
            f"Emissions of the processed invoices: system {system_kg / 1000:.3f} t, "
            f"truth {processed_truth_kg / 1000:.3f} t, deviation {deviation:+.2f} %"
        )
    if ideal_kg_total > 0:
        print(f"Coverage of the ideal total: {processed_truth_kg / ideal_kg_total * 100:.1f} %")


if __name__ == "__main__":
    main()
