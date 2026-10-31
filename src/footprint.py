"""One workbook for a folder of invoices: confirmed emissions, indicative values and a summary."""

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font

from src.factors import load_factors, to_factor_unit
from src.pipeline import mark_duplicates, process_pdf

FOOTPRINT_COLUMNS = [
    "invoice_id", "status", "supplier", "category", "scope", "period_start", "period_end",
    "quantity", "unit", "total_amount", "currency", "emission_factor", "factor_unit",
    "kg_co2e", "t_co2e", "indicative_kg_co2e", "reasons", "readings",
]
READ_FIELDS = [
    "supplier", "category", "period_start", "period_end", "quantity", "unit", "total_amount", "currency",
]
CHECKED_FIELDS = ["invoice_type", "fuel_type", "quantity", "unit"]
FILL_FROM_LLM = ["supplier", "period_start", "period_end", "total_amount", "currency"]
ENERGY_BY_TYPE = {"electricity": "grid_electricity", "natural_gas": "natural_gas"}
CATEGORY_BY_TYPE = {"electricity": "electricity", "natural_gas": "natural gas"}


def invoice_id_of(file_name):
    """The file name without its extension."""
    return Path(file_name).stem


def category_of(invoice_type, fuel_type):
    """A readable category: electricity, natural gas or fuel (diesel)."""
    if invoice_type == "fuel":
        return f"fuel ({fuel_type})" if fuel_type else "fuel"
    return CATEGORY_BY_TYPE.get(invoice_type)


def lookup_factor(invoice_type, fuel_type, quantity, unit, factors):
    """The one factor row that fits, and the quantity in that row's unit (None if nothing fits)."""
    if invoice_type is None or quantity is None or unit is None:
        return None
    energy = fuel_type if invoice_type == "fuel" else ENERGY_BY_TYPE.get(invoice_type)
    if energy is None:
        return None
    converted_quantity, converted_unit = to_factor_unit(quantity, unit)
    match = factors[
        (factors["activity_type"] == invoice_type)
        & (factors["energy_or_fuel"] == energy)
        & (factors["unit"] == converted_unit)
    ]
    if len(match) != 1:
        return None
    return match.iloc[0], converted_quantity


def blocks_indicative(reasons):
    """Reasons that make an indicative value misleading: the fuel, the unit or the quantity was not confirmed."""
    return any(
        reason.startswith(("fuel_type:", "quantity:", "unit:")) or "is not valid for" in reason
        for reason in reasons
    )


def conflicting_readings(candidates):
    """Critical fields where both readers found a value and the values differ."""
    parts = []
    for field in CHECKED_FIELDS:
        regex_value, llm_value = candidates[field]
        if regex_value is not None and llm_value is not None and regex_value != llm_value:
            parts.append(f"{field}: regex={regex_value} | llm={llm_value}")
    return "; ".join(parts)


def build_row(result, factors):
    """One workbook row. What was not read stays empty. Only processed invoices get a confirmed emission."""
    fields = result.get("fields") or {}
    candidates = result.get("candidates") or {}
    reasons = list(result.get("reasons") or [])
    processed = result["status"] == "processed"

    def value(name):
        found = fields.get(name)
        if found is None and name in FILL_FROM_LLM and name in candidates:
            found = candidates[name][1]
        return found

    row = {column: None for column in FOOTPRINT_COLUMNS}
    row.update(
        invoice_id=invoice_id_of(result["file"]),
        status="processed" if processed else "human review",
        supplier=value("supplier"),
        category=category_of(fields.get("invoice_type"), fields.get("fuel_type")),
        period_start=value("period_start"),
        period_end=value("period_end"),
        quantity=fields.get("quantity"),
        unit=fields.get("unit"),
        total_amount=value("total_amount"),
        currency=value("currency"),
        reasons="; ".join(reasons),
        readings=conflicting_readings(candidates) if candidates else "",
    )
    if processed:
        emission = result["emission"]
        row.update(
            scope=emission["scope"],
            emission_factor=emission["factor"],
            factor_unit=emission["factor_unit"],
            kg_co2e=round(emission["kg_co2e"], 3),
            t_co2e=round(emission["t_co2e"], 6),
        )
    elif fields and not blocks_indicative(reasons):
        found = lookup_factor(
            fields.get("invoice_type"), fields.get("fuel_type"),
            fields.get("quantity"), fields.get("unit"), factors,
        )
        if found is not None:
            factor_row, quantity_in_factor_unit = found
            factor = float(factor_row["factor"])
            row.update(
                scope=int(factor_row["scope"]),
                emission_factor=factor,
                factor_unit=factor_row["factor_unit"],
                indicative_kg_co2e=round(quantity_in_factor_unit * factor, 3),
            )
    return row


def footprint_table(results, factors):
    """All invoices in one table, processed ones first."""
    rows = [build_row(result, factors) for result in results]
    rows.sort(key=lambda row: row["status"] != "processed")
    return pd.DataFrame(rows, columns=FOOTPRINT_COLUMNS)


def reason_key(reason):
    """The kind of a review reason: the text before the first colon."""
    if reason.startswith("possible duplicate"):
        return "possible duplicate"
    if ":" in reason:
        return reason.split(":", 1)[0]
    return reason


def footprint_summary(results, factors):
    """Counts, totals, how much was read and why invoices went to review."""
    rows = [build_row(result, factors) for result in results]
    total = len(results)
    processed_rows = [row for row in rows if row["status"] == "processed"]
    review_rows = [row for row in rows if row["status"] != "processed"]
    crashed = sum(1 for result in results if result["status"] == "crash")
    with_value = [row for row in review_rows if row["indicative_kg_co2e"] is not None]
    share = round(100 * len(processed_rows) / total, 1) if total else 0.0

    def confirmed(scope=None):
        return round(
            sum(row["t_co2e"] for row in processed_rows if scope is None or row["scope"] == scope), 3
        )

    lines = [
        ("PDFs found", total),
        ("Emission confirmed (invoices)", len(processed_rows)),
        ("Emission confirmed (%)", share),
        ("Human review (invoices)", len(review_rows)),
        ("of which could not be processed", crashed),
        ("Confirmed emissions (tCO2e)", confirmed()),
        ("Confirmed Scope 1 (tCO2e)", confirmed(1)),
        ("Confirmed Scope 2 (tCO2e)", confirmed(2)),
        (
            "Indicative emissions, not confirmed (tCO2e)",
            round(sum(row["indicative_kg_co2e"] for row in with_value) / 1000, 3),
        ),
        ("Human review with indicative value", len(with_value)),
        ("Human review without indicative value", len(review_rows) - len(with_value)),
    ]
    for field in READ_FIELDS:
        read = sum(1 for row in rows if row[field] is not None)
        lines.append((f"Read: {field}", f"{read} of {total}"))

    counts = {}
    for result in results:
        if result["status"] == "processed":
            continue
        for key in {reason_key(reason) for reason in result.get("reasons") or []}:
            counts[key] = counts.get(key, 0) + 1
    for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append((f"Review reason: {key}", count))

    lines += [
        ("Note", "Confirmed emissions only count invoices the pipeline approved."),
        ("Note", "Read means at least one reader found a value. For human review rows it is not confirmed."),
        ("Note", "Indicative values are unconfirmed readings times the factor. A human must check them."),
        ("Note", "Factors are UK DESNZ 2025 and are applied to every invoice, whatever the country."),
    ]
    return pd.DataFrame(lines, columns=["metric", "value"])


def write_footprint_workbook(results, factors, path):
    """Write the Footprint and Summary sheets. Human review rows are grey and italic."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = footprint_table(results, factors)
    summary = footprint_summary(results, factors)
    status_column = FOOTPRINT_COLUMNS.index("status") + 1
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Footprint", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            for column in sheet.columns:
                longest = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column)
                sheet.column_dimensions[column[0].column_letter].width = min(longest + 2, 60)
            for cell in sheet[1]:
                cell.font = Font(bold=True)
        footprint = writer.sheets["Footprint"]
        footprint.auto_filter.ref = footprint.dimensions
        for row_number in range(2, footprint.max_row + 1):
            if footprint.cell(row=row_number, column=status_column).value != "processed":
                for cell in footprint[row_number]:
                    cell.font = Font(italic=True, color="808080")
    return path


def safe_process(pdf_path, factors, process=process_pdf):
    """Run the pipeline on one PDF. A crash becomes a human review result, not a stop."""
    try:
        return process(pdf_path, factors=factors)
    except Exception as error:
        return {
            "file": Path(pdf_path).name,
            "status": "crash",
            "reasons": [f"could not process: {type(error).__name__}: {error}"],
            "suggestions": {},
            "fields": None,
            "candidates": None,
            "emission": None,
        }


def run_folder(pdf_dir, out_path, factors=None, process=process_pdf):
    """Process every PDF in a folder and write the workbook. Returns the pipeline results."""
    pdf_dir = Path(pdf_dir)
    paths = sorted(path for path in pdf_dir.iterdir() if path.suffix.lower() == ".pdf")
    if not paths:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")
    factors = load_factors() if factors is None else factors
    raw = [safe_process(path, factors, process) for path in paths]
    if all(result["status"] == "crash" for result in raw):
        raise RuntimeError(f"Every invoice failed. Is Ollama running? First error: {raw[0]['reasons'][0]}")
    checked = mark_duplicates([result for result in raw if result["status"] != "crash"])
    by_file = {result["file"]: result for result in checked}
    results = [by_file.get(result["file"], result) for result in raw]
    write_footprint_workbook(results, factors, out_path)
    return results
