"""v2 Scope 2 emissions for UK electricity invoices: location-based and market-based.

Both are reported for every processed invoice (dual reporting, GHG Protocol Scope 2 Guidance).
Location-based: confirmed kWh x the grid factor. Market-based: 0 only with REGO evidence for the
whole supply, review for a green claim without it, the grid average when there is no claim.
The rules are in docs/v2-electricity-design.md, "Location-based and market-based emissions".
"""

import re

from src.factors import load_factors

REGO = re.compile(r"\bregos?\b", re.I)
PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
KWH_AMOUNT = re.compile(r"([\d,]+(?:\.\d+)?)\s*kWh", re.I)
GREEN_CLAIM = re.compile(
    r"\bgreen\b|renewable|\beco\b|\bwind\b|zero carbon|low carbon|net zero|carbon neutral", re.I)
SOLAR = re.compile(r"\bsolar\b", re.I)
# A supplier's own emission claim ("your tariff saved 84.2 kg CO2"), ignored under rule 7.
SUPPLIER_CLAIM = re.compile(
    r"(saved|saving|avoided|reduc\w*|offset)\b.*\b(co2|carbon)|\b(co2|carbon)\b.*\b(saved|avoided|reduc\w*|offset)",
    re.I)


def market_rule(text, import_kwh, export_kwh):
    """Returns (rule, market_basis, evidence_text, reason). rule is zero, review or same.

    Assumption: the REGO statement and its scope are on the same line of this invoice.
    A footer slogan cannot be told apart from a tariff statement by the text alone.
    """
    for line in text.splitlines():
        if not REGO.search(line) or SUPPLIER_CLAIM.search(line):
            continue
        line = line.strip()
        percents = [float(p) for p in PERCENT.findall(line)]
        amounts = [float(a.replace(",", "")) for a in KWH_AMOUNT.findall(line)]
        if not percents and not amounts:
            return "review", "unknown", line, "rego_without_scope"
        if 100 in percents or (import_kwh is not None and any(a >= import_kwh for a in amounts)):
            return "zero", "REGO", line, None
        return "review", "unknown", line, "rego_partial"

    for line in text.splitlines():
        if SUPPLIER_CLAIM.search(line):
            continue
        # With exported energy, "solar" describes the customer's own panel, not the tariff.
        if GREEN_CLAIM.search(line) or (export_kwh == 0 and SOLAR.search(line)):
            return "review", "unknown", line.strip(), "green_claim_without_rego"
    return "same", "grid_average_fallback", "", None


def grid_factor(factors=None):
    """The UK grid electricity factor row (location-based)."""
    factors = load_factors() if factors is None else factors
    rows = factors[(factors["activity_type"] == "electricity")
                   & (factors["energy_or_fuel"] == "grid_electricity") & (factors["unit"] == "kWh")]
    if len(rows) != 1:
        raise ValueError(f"expected one grid electricity factor, found {len(rows)}")
    return rows.iloc[0].to_dict()


def scope2(decision, text, factors=None):
    """Location-based and market-based emissions for one decided invoice, with the audit trail."""
    factor = grid_factor(factors)
    rule, basis, evidence, market_reason = market_rule(text, decision["import_kwh"], decision["export_kwh"])
    result = {
        "location_kg": None,
        "market_kg": None,
        "market_rule": rule,
        "market_basis": basis,
        "market_reason": market_reason,
        "evidence_text": evidence,
        "factor_value": float(factor["factor"]),
        "factor_source": factor["source"],
        "factor_year": int(factor["year"]),
        "reasons": [],
        "flags": [],
    }

    if any(SUPPLIER_CLAIM.search(line) for line in text.splitlines()):
        result["flags"].append("supplier_claim_ignored")
    if decision["export_kwh"]:
        result["flags"].append("onsite_generation_not_on_invoice")
    if decision["period"]:
        start_year, end_year = (int(day[:4]) for day in decision["period"])
        if start_year != end_year:
            result["reasons"].append("period_crosses_year")
        elif start_year != result["factor_year"]:
            result["flags"].append(f"factor_year_differs {start_year} vs {result['factor_year']}")

    if decision["status"] != "process" or result["reasons"]:
        return result

    result["location_kg"] = decision["import_kwh"] * result["factor_value"]
    if rule == "zero":
        result["market_kg"] = 0.0
    elif rule == "same":
        result["market_kg"] = result["location_kg"]
    return result
