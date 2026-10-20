import argparse
from pathlib import Path

import pandas as pd

from scripts.evaluate import judge
from src.extract_llm import extract_with_llm
from src.extract_rules import extract_fields, read_pdf_text
from src.hybrid import CRITICAL_FIELDS, merge_fields, review_reasons


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

    for _, row in truth.iterrows():
        text = read_pdf_text(pdf_dir / row["file_name"])
        regex_fields = extract_fields(text)
        llm_fields = extract_with_llm(text)
        merged = merge_fields(regex_fields, llm_fields)
        reasons = review_reasons(merged)

        llm_status = [
            judge(f, expected_value(row, f), llm_fields[f]) for f in CRITICAL_FIELDS
        ]
        llm_alone_wrong += any(s == "wrong" for s in llm_status)

        if reasons:
            review += 1
            review_unneeded += all(s == "ok" for s in llm_status)
            print(f"REVIEW {row['invoice_id']}: " + "; ".join(reasons))
        else:
            auto += 1
            status = [
                judge(f, expected_value(row, f), merged[f]["value"])
                for f in CRITICAL_FIELDS
            ]
            if any(s != "ok" for s in status):
                auto_wrong += 1
                print(f"SILENT ERROR {row['invoice_id']}")

    total = len(truth)
    print("\nHybrid policy: auto-process only when both readers confirm every critical field")
    print(f"Auto-processed:   {auto}/{total}  (silent critical errors: {auto_wrong})")
    print(f"Sent to review:   {review}/{total}  (unneeded: LLM alone had every critical field right: {review_unneeded})")
    print(f"LLM alone would have silently mis-processed: {llm_alone_wrong}/{total}")


if __name__ == "__main__":
    main()
