"""v2 pipeline: a folder of UK electricity invoices in, a three-sheet workbook out.

The LLM is not run here: a fake reader gives its answers.
"""

import csv
import shutil
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_uk_pipeline import check_folder_allowed
from src.uk_pipeline import process_uk_folder, process_uk_text
from src.uk_report import results_table, review_table, summary_table, write_uk_workbook

DEV = Path("data/uk_electricity/dev")

METER = """Period 01 Jan 2025 - 31 Jan 2025
Electricity
Tariff: Standard
METER TYPE PREV CURR USED (KWH) RATE (P) AMOUNT (£)
M1 Actual 12,450 12,910 460 26.50p £121.90
Subtotal £121.90"""


def no_llm(text):
    return {}


def broken_llm(text):
    raise ConnectionError("Ollama is not running")


def test_a_proved_invoice_is_processed_with_its_audit_trail():
    result = process_uk_text(METER, "a.pdf", no_llm)
    assert result["status"] == "process"
    assert result["location_kg"] == pytest.approx(460 * 0.177)
    assert (result["market_basis"], result["factor_year"]) == ("grid_average_fallback", 2025)
    assert result["period_start"] == "2025-01-01" and result["import_kwh"] == 460


def test_an_llm_that_fails_does_not_stop_the_run():
    result = process_uk_text(METER, "a.pdf", broken_llm)
    assert result["status"] == "process" and "llm_unavailable" in result["flags"]


def test_an_unreadable_pdf_goes_to_review_and_the_others_continue(tmp_path):
    (tmp_path / "bad.pdf").write_bytes(b"not a pdf")
    shutil.copy(DEV / "UK Electricity Bill 01 - Brown Power (Jan 2025).pdf", tmp_path / "good.pdf")
    results = {r["file"]: r for r in process_uk_folder(tmp_path, no_llm)}
    assert results["bad.pdf"]["status"] == "review"
    assert results["bad.pdf"]["reasons"][0].startswith("crash ")
    assert results["good.pdf"]["status"] == "process"


def test_a_second_copy_of_an_invoice_goes_to_review(tmp_path):
    for name in ("a.pdf", "b.pdf"):
        shutil.copy(DEV / "UK Electricity Bill 01 - Brown Power (Jan 2025).pdf", tmp_path / name)
    results = process_uk_folder(tmp_path, no_llm)
    assert [r["status"] for r in results] == ["process", "review"]
    assert results[1]["reasons"] == ["possible_duplicate a.pdf"]
    assert results[1]["location_kg"] is None


def test_a_green_claim_without_rego_is_processed_and_its_evidence_goes_to_the_queue():
    text = METER.replace("Tariff: Standard", "Tariff: Green Electricity")
    results = [process_uk_text(text, "green.pdf", no_llm)]
    assert len(results_table(results)) == 1 and pd.isna(results_table(results)["market_kg"][0])
    queue = review_table(results)
    assert list(queue["check"]) == ["market_based_evidence"]


@pytest.mark.parametrize("path", ["data/uk_electricity/unseen/known_layouts", "data/uk_electricity/unseen"])
def test_the_unseen_set_needs_the_official_run_flag(path):
    with pytest.raises(SystemExit):
        check_folder_allowed(path, official_run=False)
    check_folder_allowed(path, official_run=True)


def test_the_dev_set_is_always_allowed():
    check_folder_allowed("data/uk_electricity/dev", official_run=False)


# The dev folder, with an LLM that returns nothing: only the arithmetic confirms values.

with open("tests/ground_truth_uk_electricity_dev.csv", newline="", encoding="utf-8") as f:
    KEY = {row["file_name"]: row for row in csv.DictReader(f)}


@pytest.fixture(scope="module")
def dev_results():
    return process_uk_folder(DEV, no_llm)


def test_the_dev_outcomes_match_the_key(dev_results):
    assert {r["file"]: r["status"] for r in dev_results} == {name: row["expected_outcome"] for name, row in KEY.items()}


def test_the_dev_workbook_has_the_expected_rows_and_totals(dev_results, tmp_path):
    path = write_uk_workbook(dev_results, tmp_path / "uk.xlsx")
    sheets = pd.read_excel(path, sheet_name=None)
    assert list(sheets) == ["Results", "Review queue", "Summary"]
    assert len(sheets["Results"]) == 6
    assert len(sheets["Review queue"]) == 7  # 6 invoices + the D-04 market-based evidence
    summary = dict(zip(summary_table(dev_results)["metric"], summary_table(dev_results)["value"]))
    expected_location = sum(float(r["kg_co2e_location_based"]) for r in KEY.values() if r["expected_outcome"] == "process")
    assert summary["Location-based (tCO2e)"] == pytest.approx(expected_location / 1000, abs=0.001)
    assert (summary["Invoices"], summary["Processed automatically"], summary["Sent to review"]) == (12, 6, 6)
    assert summary["Crashes"] == 0
