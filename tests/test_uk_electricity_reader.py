"""v2 regex reader: energy type and billing period.

The rules are in docs/v2-electricity-design.md, "The regex reader". The short texts are invented.
"""

import csv

import pytest

from src.extract_rules import read_pdf_text
from src.uk_electricity import read_consumption, read_energy_type, read_period

JAN = ("2025-01-01", "2025-01-31")


# Period

@pytest.mark.parametrize("text", [
    "Billing period 01 Jan 2025 – 31 Jan 2025",
    "Supply period: 01 Jan 2025 - 31 Jan 2025",
    "Charges for 1 January 2025 to 31 January 2025",
    "Period 01/01/2025 - 31/01/2025",
    "Dates: 2025-01-01 to 2025-01-31",
])
def test_the_one_date_range_is_the_period_whatever_the_label_or_format(text):
    assert read_period(text) == (JAN, None)


def test_the_same_range_printed_twice_is_one_period():
    assert read_period("01 Jan 2025 - 31 Jan 2025\nUsage 01 Jan 2025 - 31 Jan 2025") == (JAN, None)


def test_a_single_date_is_not_a_period():
    assert read_period("Issue date 02 Feb 2025") == (None, "period_not_found")


def test_two_different_ranges_go_to_review():
    text = "01 Jan 2025 - 31 Jan 2025\n01 Feb 2025 - 28 Feb 2025"
    assert read_period(text) == (None, "period_ambiguous")


def test_an_end_before_the_start_goes_to_review():
    assert read_period("31 Jan 2025 - 01 Jan 2025") == (None, "period_invalid")


# Energy type

@pytest.mark.parametrize("text", [
    "Electricity charges",
    "MPAN 12 3456 7890 123",
    "Supply number 12 3456 7890\n123",  # the MPAN core wraps onto the next line
])
def test_an_electricity_marker_gives_electricity(text):
    assert read_energy_type(text) == ("electricity", None)


def test_kwh_alone_is_not_a_marker():
    assert read_energy_type("Used 450 kWh") == (None, "energy_type_unknown")


@pytest.mark.parametrize("text", ["Electricity and gas", "Electricity\nMPRN 1234567", "Electricity 450 m3"])
def test_a_gas_marker_goes_to_review(text):
    assert read_energy_type(text) == (None, "gas_marker_found")


# Dev invoices

with open("tests/ground_truth_uk_electricity_dev.csv", newline="", encoding="utf-8") as f:
    ROWS = list(csv.DictReader(f))


@pytest.mark.parametrize("row", ROWS, ids=[r["invoice_id"] for r in ROWS])
def test_the_dev_invoices_give_the_key_type_and_period(row):
    text = read_pdf_text(f"data/uk_electricity/dev/{row['file_name']}")
    assert read_energy_type(text) == ("electricity", None)
    assert read_period(text) == ((row["period_start"], row["period_end"]), None)


# Consumption (rules 1, 2, 3, 5 and 6)

METER = """METER TYPE PREV CURR USED (KWH) RATE (P) AMOUNT (£)
M1 Actual 1,000 1,300 300 20.00p £60.00
Standing Charge (30 days @ 40.00p/day) 40.00p £12.00
Subtotal £72.00
VAT @ 5.0% £3.60"""


def test_the_used_column_is_consumption_not_a_meter_reading():
    reading, reasons = read_consumption(METER)
    assert (reading["import_kwh"], reading["export_kwh"], reading["confirmed"], reasons) == (300, 0, True, [])


def test_day_and_night_lines_are_added_and_days_are_not_kwh():
    text = ("Day Rate 200 25.00p £50.00\nNight Rate 100 15.00p £15.00\n"
            "Standing Charge (30 days) 30 days 40.00p £12.00\nNet Total £77.00")
    reading, reasons = read_consumption(text)
    assert (reading["import_kwh"], reading["confirmed"], reasons) == (300, True, [])


def test_a_missing_line_fails_the_net_check():
    text = "Day Rate 200 25.00p £50.00\nNight Rate 100 15.00p £15.00\nNet Total £90.00"
    reading, reasons = read_consumption(text)
    assert reading["confirmed"] is False and "net_mismatch 65.00 vs 90.00" in reasons


def test_without_a_net_line_the_value_is_not_confirmed():
    reading, reasons = read_consumption("Day Rate 200 25.00p £50.00")
    assert (reading["import_kwh"], reading["confirmed"], reasons) == (200, False, ["net_not_found"])


def test_a_line_whose_arithmetic_fails_is_not_used():
    reading, reasons = read_consumption("Day Rate 200 25.00p £55.00\nNet £55.00")
    assert reading["import_kwh"] is None and reasons == ["consumption_not_found"]


def test_export_is_kept_apart_and_never_taken_off():
    text = "Import 1,000 1,300 300 20.00p £60.00\nExport 500 600 -100 -10.00p -£10.00\nSubtotal Net £50.00"
    reading, reasons = read_consumption(text)
    assert (reading["import_kwh"], reading["export_kwh"], reading["confirmed"], reasons) == (300, 100, True, [])


def test_readings_that_do_not_match_the_used_column_go_to_review():
    reading, reasons = read_consumption("M1 Actual 1,000 1,250 300 20.00p £60.00\nSubtotal £60.00")
    assert reading["confirmed"] is False and "readings_mismatch 250 vs 300" in reasons


def test_a_labelled_value_is_never_confirmed_on_its_own():
    text = "Previous reading 1,000 kWh\nCurrent reading 1,300 kWh\nConsumption for period 300 kWh"
    reading, reasons = read_consumption(text)
    assert (reading["import_kwh"], reading["confirmed"], reasons) == (300, False, ["label_only"])


def test_labelled_readings_that_contradict_the_consumption_go_to_review():
    text = "Previous reading 1,000\nCurrent reading 1,250\nConsumption 300 kWh"
    assert "readings_mismatch 250 vs 300" in read_consumption(text)[1]


def test_a_consumption_equal_to_a_meter_reading_goes_to_review():
    text = "Previous reading 1,000\nCurrent reading 1,300\nUsage 1,000 kWh"
    assert "quantity_is_a_reading 1000" in read_consumption(text)[1]


def test_priced_lines_and_a_label_that_disagree_go_to_review():
    text = "Day Rate 300 20.00p £60.00\nNet £60.00\nTotal usage 280 kWh"
    reading, reasons = read_consumption(text)
    assert reading["confirmed"] is False and "consumption_conflict 300 vs 280" in reasons


def test_no_consumption_goes_to_review():
    reading, reasons = read_consumption("Amount due £50.00")
    assert reading["import_kwh"] is None and reasons == ["consumption_not_found"]


# Dev invoices: kWh and export match the key; L1 to L4 are confirmed, L5 goes to review
CONFIRMED = {"D-01", "D-02", "D-03", "D-04", "D-05", "D-06"}


@pytest.mark.parametrize("row", ROWS, ids=[r["invoice_id"] for r in ROWS])
def test_the_dev_invoices_give_the_key_consumption(row):
    reading, reasons = read_consumption(read_pdf_text(f"data/uk_electricity/dev/{row['file_name']}"))
    assert reading["import_kwh"] == pytest.approx(float(row["import_kwh"]))
    assert reading["export_kwh"] == pytest.approx(float(row["export_kwh"]))
    if row["invoice_id"] in CONFIRMED:
        assert reading["confirmed"] and reasons == []
    else:
        assert not reading["confirmed"] and any(r.startswith("readings_mismatch") for r in reasons)
