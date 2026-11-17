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


# Consumption (rules 1, 2, 3, 5 and 6 in docs/v2-electricity-design.md)

NUM = r"-?[\d,]+(?:\.\d+)?"
# quantity, optional "kWh", rate in pence ("p" or "p/kWh"), amount in pounds
PRICED = re.compile(rf"(?<![\d,.])({NUM})\s*(?:kWh\s+)?({NUM})\s*p(?:/kWh)?\s+(-?£{NUM}|£-?{NUM})", re.I)
NOT_ENERGY = re.compile(r"standing|capacity|\bdays\b|/day|per day|\bccl\b|climate change levy", re.I)
STANDALONE_NUMBER = re.compile(r"(?<!\S)[\d,]+(?:\.\d+)?(?!\S)")
MONEY = re.compile(r"-?£-?[\d,]+\.\d{2}(?!\d)")
NET_LINE = re.compile(r"\bsub ?total\b|\bnet\b", re.I)
NOT_NET = re.compile(r"payable|\bdue\b|\bvat\b", re.I)
LABELLED = re.compile(rf"(?:consumption|usage|units used|energy used)[^\n£]*?({NUM})\s*kWh", re.I)
READING = re.compile(rf"(previous|current) reading\s*:?\s*({NUM})", re.I)


def number(text):
    return float(text.replace(",", "").replace("£", ""))


def show(value):
    """A number as it is written in a review reason: 24638, 263.1."""
    return f"{value:.10g}"


def checks_out(quantity, rate_pence, amount):
    """quantity x rate = amount to the penny. The sizes are compared; the sign only says import or export."""
    return abs(round(abs(quantity * rate_pence) / 100, 2) - abs(amount)) <= 0.005


def read_priced_lines(text):
    """Lines that check themselves: quantity x rate = amount. Returns imports, exports, other charges, reasons."""
    imports, exports, other_charges, reasons = [], [], [], []
    for line in text.splitlines():
        if NOT_ENERGY.search(line):
            amounts = MONEY.findall(line)
            if amounts:
                other_charges.append(number(amounts[-1]))
            continue
        for match in PRICED.finditer(line):
            quantity, rate, amount = (number(group) for group in match.groups())
            if not checks_out(quantity, rate, amount):
                continue
            readings = [number(n) for n in STANDALONE_NUMBER.findall(line[:match.start()])][-2:]
            if len(readings) == 2:
                previous, current = readings
                if abs(quantity) in (previous, current):
                    reasons.append(f"quantity_is_a_reading {show(abs(quantity))}")
                if abs((current - previous) - abs(quantity)) > 0.0005:
                    reasons.append(f"readings_mismatch {show(current - previous)} vs {show(abs(quantity))}")
            if quantity > 0 and rate > 0 and amount > 0:
                imports.append((quantity, amount))
            elif quantity < 0:
                exports.append((quantity, amount))
            else:
                reasons.append(f"line_sign_unclear {show(quantity)}")
    return imports, exports, other_charges, reasons


def net_check(lines_total, text):
    """The sum of the lines and the other charges must equal the printed net (rule 5)."""
    nets = []
    for line in text.splitlines():
        if NET_LINE.search(line) and not NOT_NET.search(line) and not NOT_ENERGY.search(line):
            amounts = MONEY.findall(line)
            if amounts:
                nets.append(number(amounts[-1]))
    if not nets:
        return "net_not_found"
    if any(abs(net - lines_total) <= 0.005 for net in nets):
        return None
    return f"net_mismatch {lines_total:.2f} vs {nets[0]:.2f}"


def read_consumption(text):
    """Import kWh from priced lines that check themselves, or from a labelled value that is never confirmed alone.

    Returns ({"import_kwh", "export_kwh", "confirmed", "source"}, reasons).
    """
    imports, exports, other_charges, reasons = read_priced_lines(text)
    priced_lines = {line for line in text.splitlines() if PRICED.search(line)}
    labelled = {number(value) for line in text.splitlines() if line not in priced_lines
                for value in LABELLED.findall(line)}

    import_kwh, source = None, None
    if imports:
        import_kwh, source = sum(quantity for quantity, _ in imports), "priced_lines"
        lines_total = sum(amount for _, amount in imports + exports) + sum(other_charges)
        problem = net_check(lines_total, text)
        if problem:
            reasons.append(problem)
        for value in labelled:
            if abs(value - import_kwh) > 0.0005:
                reasons.append(f"consumption_conflict {show(import_kwh)} vs {show(value)}")
    elif len(labelled) == 1:
        import_kwh, source = labelled.pop(), "label"
        readings = {kind.lower(): number(value) for kind, value in READING.findall(text)}
        if import_kwh in readings.values():
            reasons.append(f"quantity_is_a_reading {show(import_kwh)}")
        if len(readings) == 2 and abs(readings["current"] - readings["previous"] - import_kwh) > 0.0005:
            reasons.append(f"readings_mismatch {show(readings['current'] - readings['previous'])} vs {show(import_kwh)}")
        reasons.append("label_only")
    elif len(labelled) > 1:
        reasons.append("label_ambiguous " + " vs ".join(show(value) for value in sorted(labelled)))
    if import_kwh is None and not any(r.startswith("label_ambiguous") for r in reasons):
        reasons.append("consumption_not_found")

    export_kwh = sum(abs(quantity) for quantity, _ in exports)
    reading = {"import_kwh": import_kwh, "export_kwh": export_kwh,
               "confirmed": source == "priced_lines" and not reasons, "source": source}
    return reading, reasons
