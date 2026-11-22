"""v2 pipeline for UK electricity invoices: PDF in, decision and emissions out.

One bad invoice never stops the run: an unreadable PDF or an unexpected error goes to review
as `crash <error>`, and an LLM that is not available is recorded as `llm_unavailable`.
"""

from pathlib import Path

from src.extract_llm import extract_with_llm
from src.extract_rules import read_pdf_text
from src.factors import load_factors
from src.uk_decision import decide
from src.uk_emissions import scope2

EMISSION_FIELDS = ["location_kg", "market_kg", "market_rule", "market_basis", "market_reason",
                   "evidence_text", "factor_value", "factor_source", "factor_year"]


def empty_result(file_name):
    result = {"file": file_name, "status": "review", "reasons": [], "flags": [],
              "energy_type": None, "period_start": None, "period_end": None,
              "import_kwh": None, "export_kwh": None, "unit_shown": None,
              "llm_quantity": None, "llm_unit": None}
    result.update({field: None for field in EMISSION_FIELDS})
    return result


def process_uk_text(text, file_name="", llm_reader=extract_with_llm, factors=None):
    """Decide one invoice from its text and calculate its emissions."""
    result = empty_result(file_name)
    try:
        llm = llm_reader(text) or {}
    except Exception:  # the LLM is a second reader; without it only the arithmetic can confirm
        llm, result["flags"] = {}, ["llm_unavailable"]

    decision = decide(text, llm)
    emissions = scope2(decision, text, factors)
    period = decision["period"] or (None, None)
    result.update({
        "status": "review" if decision["reasons"] or emissions["reasons"] else "process",
        "reasons": decision["reasons"] + emissions["reasons"],
        "flags": result["flags"] + decision["flags"] + emissions["flags"],
        "energy_type": decision["energy_type"],
        "period_start": period[0],
        "period_end": period[1],
        "import_kwh": decision["import_kwh"],
        "export_kwh": decision["export_kwh"],
        "unit_shown": decision["unit_shown"],
        "llm_quantity": llm.get("quantity"),
        "llm_unit": llm.get("unit"),
    })
    result.update({field: emissions[field] for field in EMISSION_FIELDS})
    return result


def process_uk_pdf(path, llm_reader=extract_with_llm, factors=None):
    """Process one PDF. Any error is recorded as a crash and sent to review."""
    path = Path(path)
    try:
        return process_uk_text(read_pdf_text(path), path.name, llm_reader, factors)
    except Exception as error:
        result = empty_result(path.name)
        result["reasons"] = [f"crash {type(error).__name__}"]
        return result


def mark_duplicates(results):
    """A second invoice with the same period and the same kWh goes to review, so it is not counted twice."""
    seen = {}
    for result in results:
        if result["status"] != "process":
            continue
        key = (result["period_start"], result["period_end"], result["import_kwh"], result["export_kwh"])
        if key in seen:
            result["status"] = "review"
            result["reasons"].append(f"possible_duplicate {seen[key]}")
            result["location_kg"] = result["market_kg"] = None
        else:
            seen[key] = result["file"]
    return results


def process_uk_folder(folder, llm_reader=extract_with_llm, factors=None):
    """Process every PDF in a folder, in name order, then check the batch for duplicates."""
    factors = load_factors() if factors is None else factors
    results = [process_uk_pdf(pdf, llm_reader, factors) for pdf in sorted(Path(folder).glob("*.pdf"))]
    return mark_duplicates(results)
