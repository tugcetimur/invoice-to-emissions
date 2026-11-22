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
# A priced line: quantity, optional unit, optional "@", a rate, optional "=", an amount in pounds.
# The rate is in pence per kWh ("26.50p", "28.40 p/kWh") or in pounds per kWh or MWh ("£0.25 per kWh", "£250.00/MWh").
PRICED = re.compile(
    rf"(?<![\d,.])({NUM})\s*(kWh|MWh)?\s*@?\s*"
    rf"(?:({NUM})\s*p(?:/kWh)?(?![A-Za-z])|£({NUM})\s*(?:per\s*|/)(kWh|MWh))"
    rf"\s*=?\s*(-?£{NUM}|£-?{NUM})",
    re.I,
)
NOT_ENERGY = re.compile(r"standing|capacity|\bdays\b|/day|per day|\bccl\b|climate change levy", re.I)
STANDALONE_NUMBER = re.compile(r"(?<!\S)[\d,]+(?:\.\d+)?(?!\S)")
MONEY = re.compile(r"-?£-?[\d,]+\.\d{2}(?!\d)")
NET_LINE = re.compile(r"\bsub ?total\b|\bnet\b", re.I)
NOT_NET = re.compile(r"payable|\bdue\b|\bvat\b", re.I)
LABELLED = re.compile(rf"(?:consumption|usage|units used|energy used)[^\n£]*?({NUM})\s*(kWh|MWh)", re.I)
READING = re.compile(rf"(previous|current) reading\s*:?\s*({NUM})", re.I)

# The money check on a labelled value (rule 2): consumption x unit rate (+ days x daily charge) = amount.
UNIT_RATE = re.compile(rf"£({NUM})\s*(?:per|/)\s*kWh|({NUM})\s*p\s*(?:per|/)\s*kWh", re.I)
DAILY_CHARGE = re.compile(rf"£({NUM})\s*(?:per|/)\s*day|({NUM})\s*p\s*(?:per|/)\s*day", re.I)
RATE_TEXT = re.compile(r"per\s*kWh|/kWh|per\s*day|/day", re.I)
USAGE_AMOUNT = re.compile(r"usage|consumption|energy|electricity", re.I)
NOT_USAGE_AMOUNT = re.compile(r"\bvat\b|total|balance|\bdue\b|payable", re.I)


def number(text):
    return float(text.replace(",", "").replace("£", ""))


def show(value):
    """A number as it is written in a review reason: 24638, 263.1."""
    return f"{value:.10g}"


def checks_out(quantity, rate_pounds, amount):
    """quantity x rate = amount to the penny. The sizes are compared; the sign only says import or export."""
    return abs(round(abs(quantity * rate_pounds), 2) - abs(amount)) <= 0.005


def priced_line(match):
    """(kWh, unit shown, amount) for a priced line that checks itself, or None."""
    quantity, unit, pence, pounds, rate_unit, amount = match.groups()
    quantity, amount, unit = number(quantity), number(amount), (unit or "").lower()
    if pence is not None:
        rate, rate_unit = number(pence) / 100, "kwh"
    else:
        rate, rate_unit = number(pounds), rate_unit.lower()
    if unit and unit != rate_unit or not unit and rate_unit == "mwh":
        return None  # the quantity and the rate are not in the same unit
    if not checks_out(quantity, rate, amount):
        return None
    factor = 1000 if rate_unit == "mwh" else 1
    return quantity * factor, rate_unit, amount, rate


def read_priced_lines(text):
    """Lines that check themselves. Returns imports, exports, other charges, units shown, reasons."""
    imports, exports, other_charges, units, reasons = [], [], [], set(), []
    for line in text.splitlines():
        if NOT_ENERGY.search(line):
            amounts = MONEY.findall(line)
            if amounts:
                other_charges.append(number(amounts[-1]))
            continue
        for match in PRICED.finditer(line):
            found = priced_line(match)
            if found is None:
                continue
            kwh, unit, amount, rate = found
            readings = [number(n) for n in STANDALONE_NUMBER.findall(line[:match.start()])][-2:]
            if len(readings) == 2:
                previous, current = readings
                if abs(kwh) in (previous, current):
                    reasons.append(f"quantity_is_a_reading {show(abs(kwh))}")
                if abs((current - previous) - abs(kwh)) > 0.0005:
                    reasons.append(f"readings_mismatch {show(current - previous)} vs {show(abs(kwh))}")
            units.add("MWh" if unit == "mwh" else "kWh")
            if kwh > 0 and rate > 0 and amount > 0:
                imports.append((kwh, amount))
            elif kwh < 0:
                exports.append((kwh, amount))
            else:
                reasons.append(f"line_sign_unclear {show(kwh)}")
    return imports, exports, other_charges, units, reasons


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


def first_rate(pattern, text):
    """A rate in pounds, from "£0.226 per kWh" or "22.6p per kWh"."""
    match = pattern.search(text)
    if not match:
        return None
    pounds, pence = match.groups()
    return number(pounds) if pounds is not None else number(pence) / 100


def money_check(kwh, text):
    """Consumption x unit rate (+ days x daily charge) = the usage amount. None if no unit rate is printed."""
    rate = first_rate(UNIT_RATE, text)
    if rate is None:
        return None
    amount_lines = [line for line in text.splitlines()
                    if MONEY.search(line) and USAGE_AMOUNT.search(line)
                    and not RATE_TEXT.search(line) and not NOT_USAGE_AMOUNT.search(line)]
    if not amount_lines:
        return "amount_check_not_run"
    expected = []
    for line in amount_lines:
        total = kwh * rate
        if re.search(r"standing", line, re.I):
            daily, (period, _) = first_rate(DAILY_CHARGE, text), read_period(text)
            if daily is None or period is None:
                return "amount_check_not_run"
            start, end = (datetime.fromisoformat(day).date() for day in period)
            total += ((end - start).days + 1) * daily
        shown = number(MONEY.findall(line)[-1])
        if abs(round(total, 2) - shown) <= 0.005:
            return "passed"
        expected.append((round(total, 2), shown))
    return f"amount_mismatch {expected[0][0]:.2f} vs {expected[0][1]:.2f}"


def read_consumption(text):
    """Import kWh from priced lines that check themselves, or from a labelled value confirmed by rule 2.

    Returns ({"import_kwh", "export_kwh", "unit_shown", "confirmed", "source"}, reasons).
    """
    imports, exports, other_charges, units, reasons = read_priced_lines(text)
    priced_lines = {line for line in text.splitlines() if PRICED.search(line)}
    labelled = {}
    for line in text.splitlines():
        if line not in priced_lines:
            for value, unit in LABELLED.findall(line):
                kwh = number(value) * (1000 if unit.lower() == "mwh" else 1)
                labelled[kwh] = "MWh" if unit.lower() == "mwh" else "kWh"

    import_kwh, source, checks_run = None, None, 0
    if imports:
        import_kwh, source = sum(kwh for kwh, _ in imports), "priced_lines"
        lines_total = sum(amount for _, amount in imports + exports) + sum(other_charges)
        problem = net_check(lines_total, text)
        if problem:
            reasons.append(problem)
        for value in labelled:
            if abs(value - import_kwh) > 0.0005:
                reasons.append(f"consumption_conflict {show(import_kwh)} vs {show(value)}")
    elif len(labelled) == 1:
        (import_kwh, unit), = labelled.items()
        source, units = "label", {unit}
        readings = {kind.lower(): number(value) for kind, value in READING.findall(text)}
        if import_kwh in readings.values():
            reasons.append(f"quantity_is_a_reading {show(import_kwh)}")
        if len(readings) == 2:
            checks_run += 1
            if abs(readings["current"] - readings["previous"] - import_kwh) > 0.0005:
                reasons.append(f"readings_mismatch {show(readings['current'] - readings['previous'])} vs {show(import_kwh)}")
        money = money_check(import_kwh, text)
        if money is not None:
            checks_run += 1
            if money != "passed":
                reasons.append(money)
        if checks_run == 0:
            reasons.append("label_only")
    elif len(labelled) > 1:
        reasons.append("label_ambiguous " + " vs ".join(show(value) for value in sorted(labelled)))
    if import_kwh is None and not any(r.startswith("label_ambiguous") for r in reasons):
        reasons.append("consumption_not_found")

    reading = {
        "import_kwh": import_kwh,
        "export_kwh": sum(abs(kwh) for kwh, _ in exports),
        "unit_shown": ("MWh" if "MWh" in units else "kWh") if units else None,
        "confirmed": source is not None and not reasons,
        "source": source,
    }
    return reading, reasons
