"""Hybrid decision: combine the regex reader and the LLM reader field by field."""

from src.extract_rules import FIELDS

NUMERIC_FIELDS = {"quantity", "total_amount"}
# Fields that feed the emission calculation
CRITICAL_FIELDS = ["invoice_type", "fuel_type", "quantity", "unit"]


def values_agree(field, a, b):
    """True if two readers produced the same value for a field."""
    if field in NUMERIC_FIELDS:
        return abs(float(a) - float(b)) < 0.01
    return a == b


def merge_fields(regex_fields, llm_fields):
    """Merge both readers' results. Keep the status and both candidates for every field."""
    merged = {}
    for field in FIELDS:
        regex_value = regex_fields.get(field)
        llm_value = llm_fields.get(field)
        if regex_value is None and llm_value is None:
            status, value = "empty", None
        elif regex_value is None:
            status, value = "llm_only", llm_value
        elif llm_value is None:
            status, value = "regex_only", regex_value
        elif values_agree(field, regex_value, llm_value):
            status, value = "agreed", regex_value
        else:
            status, value = "conflict", None
        merged[field] = {
            "value": value,
            "status": status,
            "regex": regex_value,
            "llm": llm_value,
        }
    return merged


def review_reasons(merged):
    """Why an invoice cannot be processed automatically. An empty list means no review."""
    reasons = []
    invoice_is_fuel = merged["invoice_type"]["value"] == "fuel"
    for field in CRITICAL_FIELDS:
        item = merged[field]
        if field == "fuel_type" and item["status"] == "empty" and not invoice_is_fuel:
            continue  # not applicable to electricity and gas invoices
        if item["status"] != "agreed":
            reasons.append(
                f"{field}: {item['status']} (regex={item['regex']!r}, llm={item['llm']!r})"
            )
    return reasons
