import re
from datetime import datetime

import pdfplumber

FIELDS = [
    "invoice_type", "fuel_type", "supplier", "period_start", "period_end",
    "quantity", "unit", "total_amount", "currency",
]

DATE_FORMATS = ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"]

DESCRIPTION_RE = re.compile(r"Description:\s*(.+)")
PERIOD_RE = re.compile(
    r"(?:Billing period|Statement period|Service dates):\s*(.+?)\s+-\s+(.+)"
)
QUANTITY_RE = re.compile(
    r"(?:Consumption|Usage|Quantity used):\s*([\d,]+(?:\.\d+)?)\s*(kWh|MWh|m3|litre)"
)
TOTAL_RE = re.compile(
    r"(?:Total due|Amount payable|Total \(incl\. VAT\)):\s*([A-Z]{3})\s+([\d,]+(?:\.\d+)?)"
)


def read_pdf_text(path):
    """Read all text from a PDF, page by page."""
    with pdfplumber.open(path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def parse_date(text):
    """Try each known date format and return an ISO date string."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def classify(description):
    """Map the description line to (invoice_type, fuel_type)."""
    d = description.lower()
    if "electric" in d:
        return "electricity", None
    if "natural gas" in d:
        return "natural_gas", None
    if "diesel" in d:
        return "fuel", "diesel"
    if "petrol" in d or "unleaded" in d:
        return "fuel", "petrol"
    return None, None


def extract_fields(text):
    """Extract invoice fields from text using regular expressions."""
    fields = {name: None for name in FIELDS}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        fields["supplier"] = lines[0]

    match = DESCRIPTION_RE.search(text)
    if match:
        fields["invoice_type"], fields["fuel_type"] = classify(match.group(1))

    match = PERIOD_RE.search(text)
    if match:
        fields["period_start"] = parse_date(match.group(1))
        fields["period_end"] = parse_date(match.group(2))

    match = QUANTITY_RE.search(text)
    if match:
        fields["quantity"] = float(match.group(1).replace(",", ""))
        fields["unit"] = match.group(2)

    match = TOTAL_RE.search(text)
    if match:
        fields["currency"] = match.group(1)
        fields["total_amount"] = float(match.group(2).replace(",", ""))

    return fields


def extract_from_pdf(path):
    """Full baseline: PDF file -> dictionary of fields."""
    return extract_fields(read_pdf_text(path))
