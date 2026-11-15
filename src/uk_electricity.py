"""v2 regex reader for UK electricity invoices.

No layout-specific code: the patterns look for what every electricity invoice prints,
not for labels. Each function returns (value, reason). When the value cannot be read
safely it is None and the reason goes to the review queue.
The rules are in docs/v2-electricity-design.md, "The regex reader".
"""

import re
from datetime import datetime

DATE = r"\d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}"
RANGE = re.compile(rf"({DATE})\s*(?:–|-|\bto\b)\s*({DATE})")
DATE_FORMATS = ["%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%Y-%m-%d"]  # UK order: day before month

ELECTRICITY = re.compile(r"electric|\bmpan\b", re.I)
MPAN_CORE = re.compile(r"\b\d{2} \d{4} \d{4}\s+\d{3}\b")  # 13 digits, may wrap onto the next line
GAS = re.compile(r"\bgas\b|\bm3\b|\bmprn\b|calorific|cubic", re.I)


def parse_date(text):
    """Return an ISO date string, or None if no known format fits."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def read_period(text):
    """The billing period is the one date range on the invoice, whatever its label."""
    ranges = set()
    for start, end in RANGE.findall(text):
        start, end = parse_date(start), parse_date(end)
        if start and end:
            ranges.add((start, end))
    if not ranges:
        return None, "period_not_found"
    if len(ranges) > 1:
        return None, "period_ambiguous"
    start, end = ranges.pop()
    if end < start:
        return None, "period_invalid"
    return (start, end), None


def read_energy_type(text):
    """Electricity only when an electricity marker is printed and no gas marker is."""
    if GAS.search(text):
        return None, "gas_marker_found"
    if ELECTRICITY.search(text) or MPAN_CORE.search(text):
        return "electricity", None
    return None, "energy_type_unknown"
