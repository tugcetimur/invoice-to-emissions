"""Run the v2 pipeline on a folder of UK electricity invoices and write the workbook.

    python -m scripts.run_uk_pipeline --pdf-dir data/uk_electricity/dev --out output/uk_dev

The unseen set is locked: it runs only with --official-run (see the measurement plan in
docs/v2-electricity-design.md).
"""

import argparse
import logging
from pathlib import Path

from src.uk_pipeline import process_uk_folder
from src.uk_report import summary_table, write_uk_workbook


def check_folder_allowed(folder, official_run):
    """Refuse the unseen set unless this is the official run."""
    if "unseen" in Path(folder).parts and not official_run:
        raise SystemExit("The unseen set is locked. It runs once, with --official-run, after the code freeze.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="data/uk_electricity/dev")
    parser.add_argument("--out", default="output/uk_dev")
    parser.add_argument("--official-run", action="store_true")
    args = parser.parse_args()
    check_folder_allowed(args.pdf_dir, args.official_run)
    # pdfminer warns about missing font sizes ("Could not get FontBBox"); the text it reads is not affected.
    logging.getLogger("pdfminer").setLevel(logging.ERROR)

    results = process_uk_folder(args.pdf_dir)
    for result in results:
        line = f"{result['status'].upper():7} {result['file']}"
        if result["reasons"]:
            line += "  reasons: " + "; ".join(result["reasons"])
        if result["flags"]:
            line += "  flags: " + "; ".join(result["flags"])
        print(line)

    workbook = write_uk_workbook(results, Path(args.out) / "results.xlsx")
    print()
    print(summary_table(results).to_string(index=False))
    print(f"\nWritten to {workbook}")


if __name__ == "__main__":
    main()
