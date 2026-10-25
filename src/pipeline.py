"""End-to-end pipeline: an invoice PDF goes in, emissions or a review item comes out."""

from pathlib import Path

from src.calculate import calculate_emissions
from src.extract_llm import extract_with_llm
from src.extract_rules import extract_fields, read_pdf_text
from src.factors import load_factors
from src.hybrid import merge_fields
from src.policy import decide
from src.schema import InvoiceData


def process_text(text, file_name="", llm_reader=extract_with_llm, factors=None):
    """Read, merge and decide; if the invoice is confirmed, calculate its emissions."""
    merged = merge_fields(extract_fields(text), llm_reader(text))
    decision = decide(merged, text)

    result = {
        "file": file_name,
        "status": decision["status"],
        "reasons": list(decision["reasons"]),
        "suggestions": decision["suggestions"],
        "fields": {name: item["value"] for name, item in merged.items()},
        "candidates": {name: (item["regex"], item["llm"]) for name, item in merged.items()},
        "emission": None,
    }
    if result["status"] != "processed":
        return result

    values = result["fields"]
    if values["invoice_type"] != "fuel":
        values["fuel_type"] = None  # a stray fuel type on a non-fuel invoice is ignored

    missing = [name for name in ("period_start", "period_end") if values[name] is None]
    if missing:
        result["status"] = "needs_review"
        result["reasons"].append(
            "billing period missing: " + ", ".join(missing)
            + " (needed to assign the emissions to a reporting period)"
        )
        return result

    try:
        emission = calculate_emissions(InvoiceData(**values), factors)
    except ValueError as error:  # pydantic's ValidationError is a ValueError
        result["status"] = "needs_review"
        result["reasons"].append(f"cannot calculate: {str(error).splitlines()[0]}")
        return result

    result["emission"] = emission.model_dump()
    return result


def process_pdf(path, llm_reader=extract_with_llm, factors=None):
    """Process one invoice PDF."""
    path = Path(path)
    return process_text(read_pdf_text(path), path.name, llm_reader, factors)


def duplicate_key(fields):
    """What makes two invoices the same, or None if it cannot be judged."""
    if any(fields[name] is None for name in ("period_start", "period_end", "quantity", "unit")):
        return None
    return (
        fields["invoice_type"],
        (fields["supplier"] or "").strip().lower(),
        fields["period_start"],
        fields["period_end"],
        fields["quantity"],
        fields["unit"],
        fields["total_amount"],
    )


def mark_duplicates(results):
    """Send later copies of an already processed invoice to review, so they are not counted twice."""
    seen = {}
    for result in results:
        if result["status"] != "processed":
            continue
        key = duplicate_key(result["fields"])
        if key is None:
            continue
        if key in seen:
            result["status"] = "needs_review"
            result["reasons"].append(f"possible duplicate of {seen[key]}")
            result["emission"] = None
        else:
            seen[key] = result["file"]
    return results


def process_folder(folder, llm_reader=extract_with_llm, factors=None):
    """Process every PDF in a folder, then check the batch for duplicates."""
    if factors is None:
        factors = load_factors()
    results = [
        process_pdf(pdf, llm_reader, factors) for pdf in sorted(Path(folder).glob("*.pdf"))
    ]
    return mark_duplicates(results)
