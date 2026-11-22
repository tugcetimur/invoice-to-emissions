"""v2 workbook for UK electricity invoices: Results, Review queue and Summary."""

from pathlib import Path

import pandas as pd

RESULT_COLUMNS = [
    "file", "period_start", "period_end", "import_kwh", "unit_shown", "export_kwh",
    "location_kg", "market_kg", "market_rule", "market_basis", "market_reason", "evidence_text",
    "factor_value", "factor_source", "factor_year", "flags",
]
REVIEW_COLUMNS = [
    "file", "check", "reasons", "flags", "period_start", "period_end",
    "import_kwh_regex", "llm_quantity", "llm_unit", "evidence_text", "reviewer_note",
]


def results_table(results):
    """One row per processed invoice. A market-based review leaves market_kg empty."""
    rows = []
    for result in results:
        if result["status"] != "process":
            continue
        row = {column: result.get(column) for column in RESULT_COLUMNS}
        row["flags"] = "; ".join(result["flags"])
        rows.append(row)
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def review_row(result, check, reasons):
    return {
        "file": result["file"], "check": check, "reasons": "; ".join(reasons),
        "flags": "; ".join(result["flags"]),
        "period_start": result["period_start"], "period_end": result["period_end"],
        "import_kwh_regex": result["import_kwh"], "llm_quantity": result["llm_quantity"],
        "llm_unit": result["llm_unit"], "evidence_text": result["evidence_text"], "reviewer_note": "",
    }


def review_table(results):
    """What a human has to look at: invoices that were not processed, and market-based evidence to check."""
    rows = []
    for result in results:
        if result["status"] == "review":
            rows.append(review_row(result, "invoice", result["reasons"]))
        elif result["market_rule"] == "review":
            rows.append(review_row(result, "market_based_evidence", [result["market_reason"]]))
    return pd.DataFrame(rows, columns=REVIEW_COLUMNS)


def summary_table(results):
    """Counts and totals as a two-column table."""
    processed = [r for r in results if r["status"] == "process"]
    with_market = [r for r in processed if r["market_kg"] is not None]
    rows = [
        ("Invoices", len(results)),
        ("Processed automatically", len(processed)),
        ("Sent to review", len(results) - len(processed)),
        ("Market-based evidence to check", sum(r["market_rule"] == "review" for r in processed)),
        ("Location-based (tCO2e)", round(sum(r["location_kg"] for r in processed) / 1000, 3)),
        ("Market-based (tCO2e), invoices with a number", round(sum(r["market_kg"] for r in with_market) / 1000, 3)),
        ("Processed invoices without a market-based number", len(processed) - len(with_market)),
        ("LLM disagreed (rule 8)", sum(any(f.startswith("llm_disagreed") for f in r["flags"]) for r in results)),
        ("LLM unavailable", sum("llm_unavailable" in r["flags"] for r in results)),
        ("Crashes", sum(any(x.startswith("crash ") for x in r["reasons"]) for r in results)),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"], dtype=object)  # counts stay whole numbers


def write_uk_workbook(results, path):
    """Write the three sheets to one Excel file and return its path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        results_table(results).to_excel(writer, sheet_name="Results", index=False)
        review_table(results).to_excel(writer, sheet_name="Review queue", index=False)
        summary_table(results).to_excel(writer, sheet_name="Summary", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            for column in sheet.columns:
                longest = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column)
                sheet.column_dimensions[column[0].column_letter].width = min(longest + 2, 70)
    return path
