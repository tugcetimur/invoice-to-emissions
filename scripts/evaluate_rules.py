from pathlib import Path

import pandas as pd

from src.extract_rules import FIELDS, extract_from_pdf

TRUTH_PATH = Path("tests/ground_truth.csv")
PDF_DIR = Path("data/sample_invoices")
NUMERIC = {"quantity", "total_amount"}


def is_correct(field, expected, got):
    if expected is None:
        return got is None
    if got is None:
        return False
    if field in NUMERIC:
        return abs(float(got) - float(expected)) < 0.01
    return got == expected


def main():
    truth = pd.read_csv(TRUTH_PATH)
    correct = {f: 0 for f in FIELDS}

    for _, row in truth.iterrows():
        got = extract_from_pdf(PDF_DIR / row["file_name"])
        for f in FIELDS:
            expected = None if pd.isna(row[f]) else row[f]
            if is_correct(f, expected, got[f]):
                correct[f] += 1
            else:
                print(f"MISMATCH {row['invoice_id']} {f}: expected={expected!r} got={got[f]!r}")

    total = len(truth)
    print("\nField accuracy (regex baseline)")
    for f in FIELDS:
        print(f"{f:14s} {correct[f]}/{total}  {correct[f] / total:.0%}")


if __name__ == "__main__":
    main()
