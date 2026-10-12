import argparse
from pathlib import Path

import pandas as pd

from src.extract_rules import FIELDS, extract_from_pdf

NUMERIC = {"quantity", "total_amount"}


def judge(field, expected, got):
    """Return 'ok', 'missed' (nothing found) or 'wrong' (a wrong value found)."""
    if expected is None:
        return "ok" if got is None else "wrong"
    if got is None:
        return "missed"
    if field in NUMERIC:
        return "ok" if abs(float(got) - float(expected)) < 0.01 else "wrong"
    return "ok" if got == expected else "wrong"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", default="tests/ground_truth.csv")
    parser.add_argument("--pdf-dir", default="data/sample_invoices")
    args = parser.parse_args()

    truth = pd.read_csv(args.truth)
    pdf_dir = Path(args.pdf_dir)
    counts = {f: {"ok": 0, "missed": 0, "wrong": 0} for f in FIELDS}
    fully_correct = 0

    for _, row in truth.iterrows():
        got = extract_from_pdf(pdf_dir / row["file_name"])
        invoice_ok = True
        for f in FIELDS:
            expected = None if pd.isna(row[f]) else row[f]
            status = judge(f, expected, got[f])
            counts[f][status] += 1
            if status != "ok":
                invoice_ok = False
                twist = f" [{row['twist']}]" if "twist" in truth.columns else ""
                print(
                    f"{status.upper():6s} {row['invoice_id']} {f}: "
                    f"expected={expected!r} got={got[f]!r}{twist}"
                )
        fully_correct += invoice_ok

    total = len(truth)
    print(f"\nInvoices fully correct: {fully_correct}/{total}")
    print(f"\n{'field':14s} {'ok':>4s} {'missed':>7s} {'wrong':>6s}")
    for f in FIELDS:
        c = counts[f]
        print(f"{f:14s} {c['ok']:4d} {c['missed']:7d} {c['wrong']:6d}")


if __name__ == "__main__":
    main()
