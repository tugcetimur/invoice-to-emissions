import pandas as pd
import pytest
from openpyxl import load_workbook

from src.calculate import calculate_emissions
from src.factors import load_factors
from src.footprint import (
    build_row,
    footprint_summary,
    footprint_table,
    run_folder,
    write_footprint_workbook,
)
from src.schema import InvoiceData

FACTORS = load_factors()

CRASHED = {
    "file": "bad.pdf", "status": "crash", "reasons": ["could not process: ValueError: boom"],
    "suggestions": {}, "fields": None, "candidates": None, "emission": None,
}


def fields(**overrides):
    base = {
        "invoice_type": "electricity", "fuel_type": None, "supplier": "Aurora Power",
        "period_start": "2025-01-01", "period_end": "2025-01-31",
        "quantity": 620.0, "unit": "kWh", "total_amount": 161.2, "currency": "EUR",
    }
    return {**base, **overrides}


def llm_only(values):
    return {name: (None, value) for name, value in values.items()}


def processed(file="a.pdf", **overrides):
    values = fields(**overrides)
    return {
        "file": file, "status": "processed", "fields": values, "candidates": llm_only(values),
        "emission": {
            "scope": 2, "kg_co2e": 109.74, "t_co2e": 0.10974, "factor": 0.177,
            "factor_unit": "kgCO2e/kWh", "source": "DESNZ", "year": 2025,
        },
        "reasons": [], "suggestions": {},
    }


def review(file="b.pdf", reasons=None, candidates=None, **overrides):
    values = fields(**overrides)
    if reasons is None:
        reasons = ["invoice_type: llm_only (regex=None, llm='electricity')"]
    return {
        "file": file, "status": "needs_review", "fields": values,
        "candidates": candidates if candidates is not None else llm_only(values),
        "emission": None, "reasons": reasons, "suggestions": {},
    }


def test_a_processed_invoice_keeps_its_confirmed_emission():
    row = build_row(processed("Invoice A.pdf"), FACTORS)
    assert row["invoice_id"] == "Invoice A"
    assert row["status"] == "processed"
    assert row["category"] == "electricity"
    assert row["scope"] == 2
    assert row["emission_factor"] == 0.177
    assert row["kg_co2e"] == pytest.approx(109.74)
    assert row["indicative_kg_co2e"] is None


def test_a_review_invoice_gets_an_indicative_emission_when_the_values_fit():
    values = fields(invoice_type="natural_gas", supplier=None, quantity=1115.0, unit="m3")
    candidates = llm_only(values)
    candidates["supplier"] = ("BRITISH GAS GAS BILL", "British Gas")
    result = review("Invoice 4.pdf", candidates=candidates, invoice_type="natural_gas",
                    supplier=None, quantity=1115.0, unit="m3")
    row = build_row(result, FACTORS)
    assert row["status"] == "human review"
    assert row["supplier"] == "British Gas"
    assert row["category"] == "natural gas"
    assert row["scope"] == 1
    assert row["emission_factor"] == 2.06672
    assert row["factor_unit"] == "kgCO2e/m3"
    assert row["kg_co2e"] is None
    assert row["t_co2e"] is None
    assert row["indicative_kg_co2e"] == pytest.approx(1115 * 2.06672)


def test_no_indicative_emission_when_the_fuel_type_is_not_confirmed():
    result = review(
        "Invoice 3.pdf", invoice_type="fuel", fuel_type="diesel", quantity=620.5, unit="litre",
        reasons=["fuel_type: product line does not confirm 'diesel' (fuel_type: llm_only (regex=None, llm='diesel'))"],
    )
    row = build_row(result, FACTORS)
    assert row["category"] == "fuel (diesel)"
    assert row["quantity"] == 620.5
    assert row["indicative_kg_co2e"] is None


@pytest.mark.parametrize(
    "reasons",
    [[], ["unit: 'litre' is not valid for natural_gas invoices"]],
)
def test_no_indicative_emission_when_the_unit_does_not_fit_the_type(reasons):
    result = review("Invoice 7.pdf", reasons=reasons, invoice_type="natural_gas", quantity=850.0, unit="litre")
    assert build_row(result, FACTORS)["indicative_kg_co2e"] is None


def test_mwh_is_converted_before_the_factor_is_applied():
    row = build_row(review(quantity=2.5, unit="MWh"), FACTORS)
    assert row["indicative_kg_co2e"] == pytest.approx(2500 * 0.177)


def test_the_indicative_emission_matches_the_existing_calculation():
    invoice = InvoiceData(
        invoice_type="fuel", fuel_type="diesel", period_start="2025-03-01",
        period_end="2025-03-31", quantity=620.5, unit="litre",
    )
    expected = calculate_emissions(invoice, FACTORS).kg_co2e
    result = review(reasons=[], invoice_type="fuel", fuel_type="diesel", quantity=620.5, unit="litre")
    assert build_row(result, FACTORS)["indicative_kg_co2e"] == pytest.approx(expected, abs=0.001)


def test_values_that_were_not_read_stay_empty():
    result = {
        "file": "c.pdf", "status": "needs_review",
        "fields": {name: None for name in fields()},
        "candidates": {name: (None, None) for name in fields()},
        "emission": None, "reasons": ["quantity: empty (regex=None, llm=None)"], "suggestions": {},
    }
    row = build_row(result, FACTORS)
    assert row["invoice_id"] == "c"
    for column in ("supplier", "category", "quantity", "unit", "total_amount", "indicative_kg_co2e"):
        assert row[column] is None


def test_conflicting_readings_are_listed_and_the_value_is_left_empty():
    candidates = llm_only(fields(quantity=None))
    candidates["quantity"] = (4100.0, 520.0)
    result = review("d.pdf", candidates=candidates, quantity=None,
                    reasons=["quantity: conflict (regex=4100.0, llm=520.0)"])
    row = build_row(result, FACTORS)
    assert row["quantity"] is None
    assert row["readings"] == "quantity: regex=4100.0 | llm=520.0"
    assert row["indicative_kg_co2e"] is None


def test_a_crashed_invoice_becomes_a_human_review_row():
    row = build_row(CRASHED, FACTORS)
    assert row["invoice_id"] == "bad"
    assert row["status"] == "human review"
    assert "boom" in row["reasons"]
    assert row["quantity"] is None


def test_processed_invoices_come_first():
    table = footprint_table([review("b.pdf"), processed("a.pdf")], FACTORS)
    assert list(table.columns)[0] == "invoice_id"
    assert list(table["invoice_id"]) == ["a", "b"]
    assert list(table["status"]) == ["processed", "human review"]


def summary_of(results):
    table = footprint_summary(results, FACTORS)
    return dict(zip(table["metric"], table["value"]))


def test_summary_counts_and_totals():
    results = [processed("a.pdf"), review("b.pdf", quantity=100.0, unit="kWh"), CRASHED]
    summary = summary_of(results)
    assert summary["PDFs found"] == 3
    assert summary["Emission confirmed (invoices)"] == 1
    assert summary["Emission confirmed (%)"] == 33.3
    assert summary["Human review (invoices)"] == 2
    assert summary["of which could not be processed"] == 1
    assert summary["Confirmed emissions (tCO2e)"] == pytest.approx(0.11, abs=0.001)
    assert summary["Confirmed Scope 2 (tCO2e)"] == pytest.approx(0.11, abs=0.001)
    assert summary["Confirmed Scope 1 (tCO2e)"] == 0
    assert summary["Indicative emissions, not confirmed (tCO2e)"] == pytest.approx(0.018, abs=0.001)
    assert summary["Human review with indicative value"] == 1
    assert summary["Human review without indicative value"] == 1


def test_summary_counts_how_many_invoices_each_field_was_read_in():
    results = [processed("a.pdf"), review("b.pdf", supplier=None, quantity=None), CRASHED]
    summary = summary_of(results)
    assert summary["Read: supplier"] == "1 of 3"
    assert summary["Read: quantity"] == "1 of 3"
    assert summary["Read: currency"] == "2 of 3"
    assert summary["Read: category"] == "2 of 3"


def test_summary_counts_the_review_reasons():
    results = [
        review("a.pdf", reasons=[
            "invoice_type: llm_only (regex=None, llm='electricity')",
            "quantity: number not found in the invoice text (x)",
        ]),
        review("b.pdf", reasons=["invoice_type: llm_only (regex=None, llm='fuel')"]),
        review("c.pdf", reasons=["possible duplicate of a.pdf"]),
        processed("d.pdf"),
    ]
    summary = summary_of(results)
    assert summary["Review reason: invoice_type"] == 2
    assert summary["Review reason: quantity"] == 1
    assert summary["Review reason: possible duplicate"] == 1


def test_the_workbook_has_a_footprint_sheet_and_a_summary_sheet(tmp_path):
    path = tmp_path / "out" / "footprint.xlsx"
    write_footprint_workbook([review("b.pdf"), processed("a.pdf")], FACTORS, path)
    sheets = pd.read_excel(path, sheet_name=None)
    assert list(sheets) == ["Footprint", "Summary"]
    assert list(sheets["Footprint"]["invoice_id"]) == ["a", "b"]
    footprint = load_workbook(path)["Footprint"]
    assert not footprint["A2"].font.italic
    assert footprint["A3"].font.italic


def stub_process(path, factors=None):
    if path.name == "bad.pdf":
        raise ValueError("boom")
    return processed(path.name)


def test_run_folder_reads_every_pdf_and_survives_a_crash(tmp_path):
    for name in ("a.pdf", "bad.pdf", "notes.txt"):
        (tmp_path / name).write_text("x")
    out = tmp_path / "footprint.xlsx"
    results = run_folder(tmp_path, out, factors=FACTORS, process=stub_process)
    assert [result["file"] for result in results] == ["a.pdf", "bad.pdf"]
    table = pd.read_excel(out, sheet_name="Footprint")
    assert list(table["invoice_id"]) == ["a", "bad"]
    assert list(table["status"]) == ["processed", "human review"]


def test_run_folder_stops_when_there_is_no_pdf(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_folder(tmp_path, tmp_path / "x.xlsx", factors=FACTORS, process=stub_process)


def test_run_folder_stops_when_every_invoice_fails(tmp_path):
    (tmp_path / "bad.pdf").write_text("x")
    with pytest.raises(RuntimeError):
        run_folder(tmp_path, tmp_path / "x.xlsx", factors=FACTORS, process=stub_process)


@pytest.mark.parametrize(
    "reason",
    [
        "quantity: number not found in the invoice text (quantity: llm_only (regex=None, llm=56640.0))",
        "quantity: price per unit could not be checked (quantity: llm_only (regex=None, llm=112400.0))",
    ],
)
def test_no_indicative_emission_when_the_quantity_check_did_not_pass(reason):
    result = review(
        "Invoice 1.pdf",
        reasons=["invoice_type: llm_only (regex=None, llm='electricity')", reason],
        quantity=56640.0, unit="kWh",
    )
    row = build_row(result, FACTORS)
    assert row["quantity"] == 56640.0
    assert row["indicative_kg_co2e"] is None
