"""Validation rules that check reader output against the invoice text itself."""

import re

# A run of digits that may contain . and , (for example 404, 1,234 or 1.234,5)
NUMBER_TOKEN = re.compile(r"\d[\d.,]*\d|\d")


def number_candidates(token):
    """All numeric values a token such as '1.234,5' or '12,5' could stand for."""
    try:
        has_dot, has_comma = "." in token, "," in token
        if has_dot and has_comma:
            # The separator that comes last is the decimal one
            decimal = "." if token.rfind(".") > token.rfind(",") else ","
            thousands = "," if decimal == "." else "."
            return {float(token.replace(thousands, "").replace(decimal, "."))}
        if not has_dot and not has_comma:
            return {float(token)}
        separator = "." if has_dot else ","
        if token.count(separator) > 1:
            return {float(token.replace(separator, ""))}  # only thousands separators
        digits_after = len(token.split(separator)[1])
        as_decimal = float(token.replace(separator, "."))
        if digits_after == 3:
            return {float(token.replace(separator, "")), as_decimal}  # ambiguous
        return {as_decimal}
    except ValueError:
        return set()


def is_grounded(value, text, tolerance=0.01):
    """True if the number appears in the invoice text, whatever the separator style."""
    for token in NUMBER_TOKEN.findall(text):
        if any(abs(value - candidate) < tolerance for candidate in number_candidates(token)):
            return True
    return False


# Price per unit in EUR. The bands are deliberately wide: they only exist to catch
# gross scale errors (a factor of 100 or 1000), not unusual prices.
PRICE_BANDS = {
    ("electricity", "kWh"): (0.03, 1.5),
    ("electricity", "MWh"): (30.0, 1500.0),
    ("natural_gas", "kWh"): (0.01, 1.5),
    ("natural_gas", "m3"): (0.02, 20.0),
    ("fuel", "litre"): (0.7, 4.0),
}


def price_per_unit(total_amount, quantity):
    """Price paid per unit of quantity, or None if it cannot be computed."""
    if not total_amount or not quantity:
        return None
    return total_amount / quantity


def price_is_plausible(invoice_type, unit, quantity, total_amount):
    """True or False if the price per unit is inside its band, None if it cannot be judged."""
    band = PRICE_BANDS.get((invoice_type, unit))
    price = price_per_unit(total_amount, quantity)
    if band is None or price is None:
        return None
    low, high = band
    return low <= price <= high
