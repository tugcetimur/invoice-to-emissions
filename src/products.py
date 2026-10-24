"""Known fuel product names. Domain knowledge lives here so it can be reviewed in one place."""

from src.extract_rules import DESCRIPTION_RE

# Lowercase words that identify a fuel on the product line of an invoice.
# The list is deliberately narrow: an unfamiliar name goes to a human instead of being guessed.
FUEL_KEYWORDS = {
    "diesel": ("diesel",),
    "petrol": ("petrol", "unleaded", "gasoline"),
}


def fuel_product_check(fuel_type, text):
    """Does the product line of the invoice support the claimed fuel type?

    Returns "confirmed", "contradiction" (the product line names the other fuel)
    or "unknown_product" (no known fuel word, or no product line at all).
    """
    keywords = FUEL_KEYWORDS.get(fuel_type)
    match = DESCRIPTION_RE.search(text)
    if keywords is None or match is None:
        return "unknown_product"
    product = match.group(1).lower()
    claimed = any(word in product for word in keywords)
    other = any(
        word in product
        for fuel, words in FUEL_KEYWORDS.items()
        if fuel != fuel_type
        for word in words
    )
    if claimed and not other:
        return "confirmed"
    if other and not claimed:
        return "contradiction"
    return "unknown_product"
