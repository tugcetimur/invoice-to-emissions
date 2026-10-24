import argparse
from pathlib import Path

import pandas as pd

from scripts.evaluate import judge
from src.extract_llm import extract_with_llm
from src.extract_rules import extract_fields, read_pdf_text
from src.hybrid import CRITICAL_FIELDS, merge_fields
from src.policy import decide


def expected_value(row, field):
    return None if pd.isna(row[field]) else row[field]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", default="tests/ground_truth.csv")
    parser.add_argument("--pdf-dir", default="data/sample_invoices")
    args = parser.parse_args()

    truth = pd.read_csv(args.truth)
    pdf_dir = Path(args.pdf_dir)
    auto = auto_wrong = review = review_unneeded = llm_alone_wrong = 0
    suggested = suggested_ok = 0

    for _, row in truth.iterrows():
        text = read_pdf_text(pdf_dir / row["file_name"])
        regex_fields = extract_fields(text)
        llm_fields = extract_with_llm(text)
        merged = merge_fields(regex_fields, llm_fields)
        decision = decide(merged, text)

        critical = [
            f for f in CRITICAL_FIELDS if f != "fuel_type" or row["invoice_type"] == "fuel"
        ]
        llm_status = [judge(f, expected_value(row, f), llm_fields[f]) for f in critical]
        llm_alone_wrong += any(s == "wrong" for s in llm_status)

        if decision["status"] == "needs_review":
            review += 1
            review_unneeded += all(s == "ok" for s in llm_status)
            print(f"REVIEW {row['invoice_id']}: " + "; ".join(decision["reasons"]))
            for field, value in decision["suggestions"].items():
                suggested += 1
                suggested_ok += judge(field, expected_value(row, field), value) == "ok"
                print(f"       suggestion {field} = {value!r}")
        else:
            auto += 1
            status = [judge(f, expected_value(row, f), merged[f]["value"]) for f in critical]
            if any(s != "ok" for s in status):
                auto_wrong += 1
                print(f"SILENT ERROR {row['invoice_id']}")
            else:
                print(f"AUTO   {row['invoice_id']}")

    total = len(truth)
    print("\nPolicy: automatic only when every critical field is confirmed")
    print(f"Auto-processed:   {auto}/{total}  (silent critical errors: {auto_wrong})")
    print(f"Sent to review:   {review}/{total}  (unneeded: LLM alone had every critical field right: {review_unneeded})")
    print(f"Suggestions given: {suggested}  (correct: {suggested_ok})")
    print(f"LLM alone would have silently mis-processed: {llm_alone_wrong}/{total}")


if __name__ == "__main__":
    main()
