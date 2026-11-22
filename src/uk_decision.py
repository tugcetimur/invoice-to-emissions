"""v2 decision for UK electricity invoices: the regex reader and the LLM reader together.

The regex reader proves its values with the invoice's own arithmetic. The LLM is a second
reader. Rule 2: a value is confirmed when the invoice checks itself, or, when no check can
run, when both readers read the same number. Rule 8: a value proved by the arithmetic wins
over an LLM value that does not fit the arithmetic; the conflict is kept as a flag.
The rules are in docs/v2-electricity-design.md.

`reasons` stop the invoice (review). `flags` are recorded and do not stop it.
"""

from src.uk_electricity import (
    NOT_ENERGY,
    PRICED,
    READING,
    STANDALONE_NUMBER,
    checks_out,
    money_check,
    number,
    read_consumption,
    read_energy_type,
    read_period,
    show,
)

# Problems that only say no check could run. With them, both readers must agree.
NO_CHECK = {"label_only", "net_not_found"}


def llm_kwh(llm):
    """The LLM quantity in kWh, or None."""
    quantity = llm.get("quantity")
    if quantity is None:
        return None
    return quantity * 1000 if llm.get("unit") == "MWh" else quantity


def same(a, b):
    return a is not None and b is not None and abs(a - b) <= 0.005


def value_checks_out(kwh, text):
    """Does this kWh value fit the invoice's arithmetic anywhere (a priced line, the readings, the money)?"""
    for line in text.splitlines():
        if NOT_ENERGY.search(line):
            continue
        for match in PRICED.finditer(line):
            _, _, pence, pounds, rate_unit, amount = match.groups()
            if pence is not None:
                rate = number(pence) / 100
            else:
                rate = number(pounds) / (1000 if rate_unit.lower() == "mwh" else 1)
            if checks_out(kwh, rate, number(amount)):
                return True
            readings = [number(n) for n in STANDALONE_NUMBER.findall(line[:match.start()])][-2:]
            if len(readings) == 2 and same(readings[1] - readings[0], kwh):
                return True
    readings = {kind.lower(): number(value) for kind, value in READING.findall(text)}
    if len(readings) == 2 and same(readings["current"] - readings["previous"], kwh):
        return True
    return money_check(kwh, text) == "passed"


def decide(text, llm):
    """Decide whether the critical fields are confirmed. Returns the values, the status, reasons and flags."""
    reasons, flags = [], []

    energy_type, problem = read_energy_type(text)
    if problem:
        reasons.append(problem)
    elif llm.get("invoice_type") not in (None, "electricity"):
        reasons.append(f"energy_type_conflict {llm['invoice_type']} vs electricity")

    period, problem = read_period(text)
    if problem:
        reasons.append(problem)
    else:
        for llm_date, regex_date in zip((llm.get("period_start"), llm.get("period_end")), period):
            if llm_date is not None and llm_date != regex_date:
                reasons.append(f"period_conflict {llm.get('period_start')}..{llm.get('period_end')} "
                               f"vs {period[0]}..{period[1]}")
                break

    reading, problems = read_consumption(text)
    regex_value, llm_value = reading["import_kwh"], llm_kwh(llm)
    if reading["confirmed"]:
        if llm_value is not None and not same(llm_value, regex_value):
            if value_checks_out(llm_value, text):
                reasons.append(f"two_values_check_out {show(llm_value)} vs {show(regex_value)}")
            else:
                flags.append(f"llm_disagreed {show(llm_value)} vs {show(regex_value)}")
    elif regex_value is not None and set(problems) <= NO_CHECK:
        if llm_value is None:
            reasons += problems + ["llm_missing"]
        elif not same(llm_value, regex_value):
            reasons += problems + [f"llm_disagreed {show(llm_value)} vs {show(regex_value)}"]
    else:
        reasons += problems
        if regex_value is None and llm_value is not None:
            reasons.append(f"llm_only {show(llm_value)}")

    return {
        "status": "review" if reasons else "process",
        "energy_type": energy_type,
        "period": period,
        "import_kwh": regex_value,
        "export_kwh": reading["export_kwh"],
        "unit_shown": reading["unit_shown"],
        "reasons": reasons,
        "flags": flags,
    }
