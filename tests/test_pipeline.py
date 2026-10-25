import pytest

from src.pipeline import mark_duplicates, process_folder, process_text

ELECTRICITY = (
    "Northwind Energy\nInvoice no: T-01\nDescription: Electricity supply\n"
    "Billing period: 01 Apr 2025 - 30 Apr 2025\nConsumption: 404 kWh\nTotal due: EUR 115.30\n"
)
FUEL = (
    "RoadStar Petrol\nInvoice no: T-02\nDescription: Diesel\n"
    "Billing period: 01 Jun 2025 - 30 Jun 2025\nConsumption: 900 litre\nTotal due: EUR 1570.00\n"
)
ELECTRICITY_FIELDS = {
    "invoice_type": "electricity", "fuel_type": None, "supplier": "Northwind Energy",
    "period_start": "2025-04-01", "period_end": "2025-04-30",
    "quantity": 404.0, "unit": "kWh", "total_amount": 115.3, "currency": "EUR",
}
DIESEL_FIELDS = {
    "invoice_type": "fuel", "fuel_type": "diesel", "supplier": "RoadStar Petrol",
    "period_start": "2025-06-01", "period_end": "2025-06-30",
    "quantity": 900.0, "unit": "litre", "total_amount": 1570.0, "currency": "EUR",
}


def reader(base=ELECTRICITY_FIELDS, **overrides):
    """A stand-in for the LLM reader that returns fixed fields."""
    fields = {**base, **overrides}
    return lambda text: fields


def test_confirmed_invoice_gets_an_emission():
    result = process_text(ELECTRICITY, "a.pdf", llm_reader=reader())
    assert result["status"] == "processed"
    assert result["emission"]["kg_co2e"] == pytest.approx(404 * 0.177)
    assert result["emission"]["scope"] == 2


def test_review_result_has_no_emission_but_keeps_reasons_and_candidates():
    result = process_text(ELECTRICITY, "a.pdf", llm_reader=reader(quantity=842000.0))
    assert result["status"] == "needs_review"
    assert result["emission"] is None
    assert result["reasons"]
    assert result["candidates"]["quantity"] == (404.0, 842000.0)
    assert result["suggestions"] == {"quantity": 404.0}


def test_missing_billing_period_goes_to_review():
    text = (
        "Northwind Energy\nInvoice no: T-01\nDescription: Electricity supply\n"
        "Consumption: 404 kWh\nTotal due: EUR 115.30\n"
    )
    result = process_text(text, "a.pdf", llm_reader=reader(period_start=None, period_end=None))
    assert result["status"] == "needs_review"
    assert any("billing period" in reason for reason in result["reasons"])
    assert result["emission"] is None


def test_stray_fuel_type_on_a_non_fuel_invoice_is_ignored():
    result = process_text(ELECTRICITY, "a.pdf", llm_reader=reader(fuel_type="petrol"))
    assert result["status"] == "processed"
    assert result["fields"]["fuel_type"] is None


def test_confirmed_fuel_invoice_gets_a_scope_1_emission():
    result = process_text(FUEL, "b.pdf", llm_reader=reader(DIESEL_FIELDS))
    assert result["status"] == "processed"
    assert result["emission"]["scope"] == 1
    assert result["emission"]["kg_co2e"] == pytest.approx(900 * 2.57082)


def test_second_copy_of_an_invoice_is_flagged_as_duplicate():
    results = [
        process_text(ELECTRICITY, "a.pdf", llm_reader=reader()),
        process_text(ELECTRICITY, "b.pdf", llm_reader=reader()),
    ]
    marked = mark_duplicates(results)
    assert marked[0]["status"] == "processed"
    assert marked[1]["status"] == "needs_review"
    assert any("duplicate of a.pdf" in reason for reason in marked[1]["reasons"])
    assert marked[1]["emission"] is None


def test_different_invoices_are_not_duplicates():
    results = [
        process_text(ELECTRICITY, "a.pdf", llm_reader=reader()),
        process_text(FUEL, "b.pdf", llm_reader=reader(DIESEL_FIELDS)),
    ]
    assert [r["status"] for r in mark_duplicates(results)] == ["processed", "processed"]


def test_process_folder_marks_duplicates_across_files(tmp_path, monkeypatch):
    (tmp_path / "a.pdf").write_bytes(b"")
    (tmp_path / "b.pdf").write_bytes(b"")
    monkeypatch.setattr("src.pipeline.read_pdf_text", lambda path: ELECTRICITY)
    results = process_folder(tmp_path, llm_reader=reader())
    assert [r["file"] for r in results] == ["a.pdf", "b.pdf"]
    assert [r["status"] for r in results] == ["processed", "needs_review"]
