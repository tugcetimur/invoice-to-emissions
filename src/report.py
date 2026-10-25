"""Turn pipeline results into tables and an Excel workbook."""

from pathlib import Path

import pandas as pd

RESULT_COLUMNS = [
    "file", "invoice_type", "fuel_type", "supplier", "period_start", "period_end",
    "quantity", "unit", "total_amount", "currency", "scope", "kg_co2e", "t_co2e",
    "factor", "factor_unit", "factor_source", "factor_year",
]
REVIEW_FIELDS = ["invoice_type", "fuel_type", "quantity", "unit"]
REVIEW_COLUMNS = (
    ["file", "reasons", "suggestion"]
    + [f"{field}_{reader}" for field in REVIEW_FIELDS for reader in ("regex", "llm")]
    + ["reviewer_note"]
)


def results_table(results):
    """One row per processed invoice, with its emissions."""
    rows = []
    for result in results:
        if result["status"] != "processed":
            continue
        fields, emission = result["fields"], result["emission"]
        rows.append(
            {
                "file": result["file"],
                "invoice_type": fields["invoice_type"],
                "fuel_type": fields["fuel_type"],
                "supplier": fields["supplier"],
                "period_start": fields["period_start"],
                "period_end": fields["period_end"],
                "quantity": fields["quantity"],
                "unit": fields["unit"],
                "total_amount": fields["total_amount"],
                "currency": fields["currency"],
                "scope": emission["scope"],
                "kg_co2e": round(emission["kg_co2e"], 3),
                "t_co2e": round(emission["t_co2e"], 6),
                "factor": emission["factor"],
                "factor_unit": emission["factor_unit"],
                "factor_source": emission["source"],
                "factor_year": emission["year"],
            }
        )
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def review_table(results):
    """One row per invoice a human has to look at: why, both readers' values, a suggestion."""
    rows = []
    for result in results:
        if result["status"] != "needs_review":
            continue
        row = {
            "file": result["file"],
            "reasons": "; ".join(result["reasons"]),
            "suggestion": "; ".join(f"{field} = {value}" for field, value in result["suggestions"].items()),
        }
        for field in REVIEW_FIELDS:
            regex_value, llm_value = result["candidates"][field]
            row[f"{field}_regex"] = regex_value
            row[f"{field}_llm"] = llm_value
        row["reviewer_note"] = ""
        rows.append(row)
    return pd.DataFrame(rows, columns=REVIEW_COLUMNS)


def summary_table(results):
    """Counts and emission totals as a two-column table."""
    processed = results_table(results)
    total = len(results)
    if processed.empty:
        by_scope = pd.Series(dtype=float)
    else:
        by_scope = processed.groupby("scope")["t_co2e"].sum()
    rows = [
        ("Invoices", total),
        ("Processed automatically", len(processed)),
        ("Sent to review", total - len(processed)),
        ("Scope 1 (tCO2e)", round(float(by_scope.get(1, 0.0)), 3)),
        ("Scope 2 (tCO2e)", round(float(by_scope.get(2, 0.0)), 3)),
        ("Total (tCO2e)", round(float(processed["t_co2e"].sum()), 3)),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def write_workbook(results, path):
    """Write the three tables as sheets of one Excel file and return its path."""
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
