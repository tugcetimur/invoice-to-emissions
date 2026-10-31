"""Read a folder of invoice PDFs and write one footprint workbook."""

import argparse
import logging

from src.footprint import run_folder


def main():
    parser = argparse.ArgumentParser(description="Read a folder of invoice PDFs and write one footprint workbook.")
    parser.add_argument("--pdf-dir", required=True, help="Folder with the invoice PDFs")
    parser.add_argument("--out", default="output/footprint.xlsx", help="Excel file to write")
    args = parser.parse_args()

    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    results = run_folder(args.pdf_dir, args.out)

    processed = sum(1 for result in results if result["status"] == "processed")
    print(f"{len(results)} PDFs: emission confirmed for {processed}, human review for {len(results) - processed}")
    print(f"Written to {args.out}")


if __name__ == "__main__":
    main()
