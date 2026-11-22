"""v2 decision: the regex reader and the LLM reader together (rules 2 and 8).

The rules are in docs/v2-electricity-design.md. The LLM is not run here: its answers are given by hand.
"""

import csv

import pytest

from src.extract_rules import read_pdf_text
from src.uk_decision import decide

METER = """Period 01 Jan 2025 - 31 Jan 2025
Electricity
METER TYPE PREV CURR USED (KWH) RATE (P) AMOUNT (£)
M1 Actual 1,000 1,300 300 20.00p £60.00
Standing Charge (31 days @ 40.00p/day) 40.00p £12.40
Subtotal £72.40"""


def llm(quantity=None, unit="kWh", invoice_type="electricity", start="2025-01-01", end="2025-01-31"):
    return {"invoice_type": invoice_type, "quantity": quantity, "unit": unit,
            "period_start": start, "period_end": end}


def test_readers_that_agree_are_processed():
    result = decide(METER, llm(300))
    assert (result["status"], result["import_kwh"], result["reasons"], result["flags"]) == ("process", 300, [], [])


def test_a_proved_value_wins_over_an_llm_that_read_a_meter_reading():
    result = decide(METER, llm(1000))
    assert (result["status"], result["import_kwh"], result["flags"]) == ("process", 300, ["llm_disagreed 1000 vs 300"])


def test_two_values_that_both_check_out_go_to_review():
    text = ("Period 01 Jan 2025 - 31 Jan 2025\nElectricity\n"
            "Day Rate 200 25.00p £50.00\nNight Rate 100 15.00p £15.00\nNet Total £65.00")
    result = decide(text, llm(200))
    assert result["status"] == "review" and "two_values_check_out 200 vs 300" in result["reasons"]


def test_a_proved_value_needs_no_llm():
    result = decide(METER, llm(None))
    assert (result["status"], result["import_kwh"]) == ("process", 300)


LABEL = "Period 01 Jan 2025 - 31 Jan 2025\nElectricity\nConsumption 300 kWh"


def test_with_no_check_the_readers_must_agree():
    assert decide(LABEL, llm(300))["status"] == "process"


def test_with_no_check_a_disagreement_goes_to_review():
    result = decide(LABEL, llm(280))
    assert result["status"] == "review" and "llm_disagreed 280 vs 300" in result["reasons"]


def test_with_no_check_a_missing_llm_value_goes_to_review():
    result = decide(LABEL, llm(None))
    assert result["status"] == "review" and "llm_missing" in result["reasons"]


def test_a_failed_check_goes_to_review_even_when_the_readers_agree():
    text = "Period 01 Jan 2025 - 31 Jan 2025\nElectricity\nPrevious reading 1,000\nCurrent reading 1,250\nConsumption 300 kWh"
    result = decide(text, llm(300))
    assert result["status"] == "review" and "readings_mismatch 250 vs 300" in result["reasons"]


def test_an_llm_value_alone_is_never_enough():
    result = decide("Period 01 Jan 2025 - 31 Jan 2025\nElectricity\nAmount due £50.00", llm(300))
    assert result["status"] == "review" and "llm_only 300" in result["reasons"]


def test_an_llm_value_in_mwh_is_compared_in_kwh():
    assert decide(METER, llm(0.3, unit="MWh"))["flags"] == []


def test_an_llm_energy_type_that_differs_goes_to_review():
    result = decide(METER, llm(300, invoice_type="natural_gas"))
    assert result["status"] == "review" and "energy_type_conflict natural_gas vs electricity" in result["reasons"]


def test_an_llm_period_that_differs_goes_to_review():
    result = decide(METER, llm(300, start="2025-02-01", end="2025-02-28"))
    assert result["status"] == "review" and any(r.startswith("period_conflict") for r in result["reasons"])


# Dev invoices

with open("tests/ground_truth_uk_electricity_dev.csv", newline="", encoding="utf-8") as f:
    ROWS = list(csv.DictReader(f))


def dev_text(row):
    return read_pdf_text(f"data/uk_electricity/dev/{row['file_name']}")


def key_llm(row, quantity=None):
    return llm(float(row["import_kwh"]) if quantity is None else quantity,
               start=row["period_start"], end=row["period_end"])


@pytest.mark.parametrize("row", ROWS, ids=[r["invoice_id"] for r in ROWS])
def test_the_dev_invoices_follow_the_key_when_the_llm_agrees(row):
    result = decide(dev_text(row), key_llm(row))
    assert result["status"] == row["expected_outcome"]
    assert result["import_kwh"] == pytest.approx(float(row["import_kwh"]))
    assert result["export_kwh"] == pytest.approx(float(row["export_kwh"]))


# The baseline LLM read the previous meter reading on the three L1 invoices.
BASELINE_LLM = {"D-01": 12450, "D-02": 15400, "D-03": 7680}


@pytest.mark.parametrize("row", [r for r in ROWS if r["invoice_id"] in BASELINE_LLM], ids=list(BASELINE_LLM))
def test_the_l1_invoices_are_processed_when_the_llm_reads_the_previous_reading(row):
    wrong = BASELINE_LLM[row["invoice_id"]]
    result = decide(dev_text(row), key_llm(row, quantity=wrong))
    assert result["status"] == "process"
    assert result["import_kwh"] == pytest.approx(float(row["import_kwh"]))
    assert result["flags"] == [f"llm_disagreed {wrong} vs {row['import_kwh']}"]
