import json
from types import SimpleNamespace

import pytest

import src.extract_llm as llm

ALL_KEYS = [
    "invoice_type", "fuel_type", "supplier", "period_start", "period_end",
    "quantity", "unit", "total_amount", "currency",
]


def full_response(**values):
    """A model answer with every key present (null unless given)."""
    data = {key: None for key in ALL_KEYS}
    data.update(values)
    return json.dumps(data)


def fake_chat_returning(content):
    def fake_chat(**kwargs):
        return SimpleNamespace(message=SimpleNamespace(content=content))
    return fake_chat


def test_valid_response_is_parsed(monkeypatch):
    content = full_response(
        invoice_type="electricity", supplier="Green Power Ltd",
        period_start="2025-03-01", period_end="2025-03-31",
        quantity=500, unit="kWh", total_amount=150.0, currency="EUR",
    )
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert fields["invoice_type"] == "electricity"
    assert fields["quantity"] == pytest.approx(500)
    assert fields["period_start"] == "2025-03-01"


def test_malformed_response_gives_all_none(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_chat_returning("this is not json"))
    fields = llm.extract_with_llm("any text")
    assert all(value is None for value in fields.values())


def test_invalid_date_becomes_none(monkeypatch):
    content = full_response(period_start="March 2025", period_end="2025-03-31")
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert fields["period_start"] is None
    assert fields["period_end"] == "2025-03-31"


def test_null_values_stay_none(monkeypatch):
    content = full_response(invoice_type="fuel")
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert fields["invoice_type"] == "fuel"
    assert fields["quantity"] is None


def test_response_with_missing_keys_is_rejected(monkeypatch):
    content = json.dumps({"supplier": "Only One Key"})
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert all(value is None for value in fields.values())


def test_all_fields_are_required_in_schema():
    required = llm.LLMInvoice.model_json_schema().get("required", [])
    assert set(required) == set(ALL_KEYS)


def test_dates_are_converted_day_first():
    assert llm.to_iso_date("01/02/2025") == "2025-02-01"
    assert llm.to_iso_date("01 Apr 2025") == "2025-04-01"


def test_missing_or_unknown_dates_become_none():
    assert llm.to_iso_date(None) is None
    assert llm.to_iso_date("sometime in spring") is None
