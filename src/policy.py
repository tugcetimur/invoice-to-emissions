"""Decision policy: combine the hybrid statuses with the checks against the invoice text.

An invoice is processed automatically only if every critical field is confirmed,
either by both readers or by the checks. Everything else goes to a human with the
reasons and, where the checks point to a single candidate, a suggestion.
"""

from src.products import fuel_product_check
from src.schema import ALLOWED_UNITS
from src.validate import is_grounded, price_is_plausible

SINGLE_SOURCE = ("regex_only", "llm_only")


def candidates(item):
    """The distinct values the readers proposed for a field."""
    values = []
    for value in (item["regex"], item["llm"]):
        if value is not None and value not in values:
            values.append(value)
    return values


def describe(field, item):
    return f"{field}: {item['status']} (regex={item['regex']!r}, llm={item['llm']!r})"


def trusted_total(merged, text):
    """The invoice total, but only if it can be found in the invoice text."""
    found = {
        round(value, 2)
        for value in candidates(merged["total_amount"])
        if is_grounded(value, text)
    }
    return found.pop() if len(found) == 1 else None


def quantity_problem(quantity, invoice_type, unit, total, text):
    """Check a quantity against the invoice itself. None means it passed."""
    if not is_grounded(quantity, text):
        return "number not found in the invoice text"
    plausible = price_is_plausible(invoice_type, unit, quantity, total)
    if plausible is False:
        return "implausible price per unit"
    if plausible is None:
        return "price per unit could not be checked"
    return None


def decide(merged, text):
    """Decide whether an invoice can be processed automatically."""
    reasons = []
    suggestions = {}

    invoice_type = merged["invoice_type"]["value"]
    unit = merged["unit"]["value"]
    total = trusted_total(merged, text)

    # Invoice type: no independent check exists, so both readers must agree.
    item = merged["invoice_type"]
    if item["status"] != "agreed":
        reasons.append(describe("invoice_type", item))

    # Quantity: the number must be in the text and the price per unit plausible.
    item = merged["quantity"]
    quantity_ok = False
    if item["status"] == "conflict":
        passing = [
            value
            for value in candidates(item)
            if quantity_problem(value, invoice_type, unit, total, text) is None
        ]
        message = describe("quantity", item)
        if len(passing) == 1:
            suggestions["quantity"] = passing[0]
            message += f"; only {passing[0]!r} passes the checks"
        reasons.append(message)
    elif item["status"] == "empty":
        reasons.append(describe("quantity", item))
    else:
        problem = quantity_problem(item["value"], invoice_type, unit, total, text)
        if problem is None:
            quantity_ok = True
        else:
            reasons.append(f"quantity: {problem} ({describe('quantity', item)})")

    # Unit: must fit the invoice type. From a single reader it also needs the quantity check.
    item = merged["unit"]
    if item["status"] in ("conflict", "empty"):
        reasons.append(describe("unit", item))
    else:
        allowed = ALLOWED_UNITS.get(invoice_type)
        if allowed is not None and item["value"] not in allowed:
            reasons.append(f"unit: {item['value']!r} is not valid for {invoice_type} invoices")
        elif item["status"] in SINGLE_SOURCE and not quantity_ok:
            reasons.append(f"unit: {item['status']} and the quantity check did not pass")

    # Fuel type (fuel invoices only): the product line must confirm it.
    if invoice_type == "fuel":
        item = merged["fuel_type"]
        if item["status"] == "empty":
            reasons.append(describe("fuel_type", item))
        else:
            confirmed = [
                value
                for value in candidates(item)
                if fuel_product_check(value, text) == "confirmed"
            ]
            if item["status"] == "conflict":
                message = describe("fuel_type", item)
                if len(confirmed) == 1:
                    suggestions["fuel_type"] = confirmed[0]
                    message += f"; only {confirmed[0]!r} matches the product line"
                reasons.append(message)
            elif not confirmed:
                reasons.append(
                    f"fuel_type: product line does not confirm {item['value']!r} "
                    f"({describe('fuel_type', item)})"
                )

    return {
        "status": "needs_review" if reasons else "processed",
        "reasons": reasons,
        "suggestions": suggestions,
    }
