import argparse
from pathlib import Path

from src.pipeline import process_folder
from src.report import results_table, review_table, summary_table, write_workbook


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="data/sample_invoices")
    parser.add_argument("--out", default="output/pipeline")
    args = parser.parse_args()

    results = process_folder(args.pdf_dir)

    for result in results:
        if result["status"] == "needs_review":
            print(f"REVIEW {result['file']}: " + "; ".join(result["reasons"]))
            if result["suggestions"]:
                print(f"       suggestions: {result['suggestions']}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results_table(results).to_csv(out / "results.csv", index=False)
    review_table(results).to_csv(out / "review_queue.csv", index=False)
    workbook = write_workbook(results, out / "results.xlsx")

    print()
    print(summary_table(results).to_string(index=False))
    print(f"\nWritten to {out}: results.csv, review_queue.csv and {workbook.name}")


if __name__ == "__main__":
    main()
