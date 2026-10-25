import argparse
from pathlib import Path

import pandas as pd

from src.pipeline import process_folder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="data/sample_invoices")
    parser.add_argument("--out", default="output/pipeline")
    args = parser.parse_args()

    results = process_folder(args.pdf_dir)
    processed = [r for r in results if r["status"] == "processed"]
    review = [r for r in results if r["status"] == "needs_review"]

    rows = []
    for r in processed:
        e = r["emission"]
        rows.append(
            {
                "file": r["file"],
                **r["fields"],
                "scope": e["scope"],
                "kg_co2e": round(e["kg_co2e"], 3),
                "t_co2e": round(e["t_co2e"], 6),
                "factor": e["factor"],
                "factor_source": e["source"],
                "factor_year": e["year"],
            }
        )
    queue = []
    for r in review:
        print(f"REVIEW {r['file']}: " + "; ".join(r["reasons"]))
        if r["suggestions"]:
            print(f"       suggestions: {r['suggestions']}")
        queue.append(
            {
                "file": r["file"],
                "reasons": "; ".join(r["reasons"]),
                "suggestions": str(r["suggestions"]),
            }
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "results.csv", index=False)
    pd.DataFrame(queue).to_csv(out / "review_queue.csv", index=False)

    total = len(results)
    print(f"\nProcessed automatically: {len(processed)}/{total}")
    print(f"Sent to review:          {len(review)}/{total}")
    if rows:
        df = pd.DataFrame(rows)
        print(f"Total of processed invoices: {df['t_co2e'].sum():.3f} tCO2e")
        print(df.groupby("scope")["t_co2e"].sum().round(3))
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
