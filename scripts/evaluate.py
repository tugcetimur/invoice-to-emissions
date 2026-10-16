import argparse
import time
from pathlib import Path

import pandas as pd

from src.extract_rules import FIELDS

NUMERIC = {"quantity", "total_amount"}
# Fields that feed the emission calculation
CRITICAL = ["invoice_type", "fuel_type", "quantity", "unit"]


def get_extractor(method):
    if method == "rules":
        from src.extract_rules import extract_from_pdf
    elif method == "llm":
        from src.extract_llm import extract_from_pdf
    else:
        raise ValueError(f"Unknown method: {method}")
    return extract_from_pdf


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
    parser.add_argument("--method", choices=["rules", "llm"], default="rules")
    parser.add_argument("--truth", default="tests/ground_truth.csv")
    parser.add_argument("--pdf-dir", default="data/sample_invoices")
    args = parser.parse_args()

    extract = get_extractor(args.method)
    truth = pd.read_csv(args.truth)
    pdf_dir = Path(args.pdf_dir)
    counts = {f: {"ok": 0, "missed": 0, "wrong": 0} for f in FIELDS}
    fully_correct = critical_ok = critical_wrong = 0
    started = time.time()

    for _, row in truth.iterrows():
        got = extract(pdf_dir / row["file_name"])
        statuses = {}
        for f in FIELDS:
            expected = None if pd.isna(row[f]) else row[f]
            status = judge(f, expected, got[f])
            statuses[f] = status
            counts[f][status] += 1
            if status != "ok":
                twist = f" [{row['twist']}]" if "twist" in truth.columns else ""
                print(
                    f"{status.upper():6s} {row['invoice_id']} {f}: "
                    f"expected={expected!r} got={got[f]!r}{twist}"
                )
        critical = [statuses[f] for f in CRITICAL]
        fully_correct += all(s == "ok" for s in statuses.values())
        critical_ok += all(s == "ok" for s in critical)
        critical_wrong += any(s == "wrong" for s in critical)

    elapsed = time.time() - started
    total = len(truth)
    print(f"\nMethod: {args.method}")
    print(f"Invoices fully correct (all fields):   {fully_correct}/{total}")
    print(f"Invoices with all critical fields ok:  {critical_ok}/{total}")
    print(f"Invoices with a WRONG critical field:  {critical_wrong}/{total}")
    print(f"Average time per invoice: {elapsed / total:.1f} s")
    print(f"\n{'field':14s} {'ok':>4s} {'missed':>7s} {'wrong':>6s}")
    for f in FIELDS:
        c = counts[f]
        print(f"{f:14s} {c['ok']:4d} {c['missed']:7d} {c['wrong']:6d}")


if __name__ == "__main__":
    main()
