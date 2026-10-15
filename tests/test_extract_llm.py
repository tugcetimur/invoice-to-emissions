import json
from types import SimpleNamespace

import pytest

import src.extract_llm as llm


def fake_chat_returning(content):
    def fake_chat(**kwargs):
        return SimpleNamespace(message=SimpleNamespace(content=content))
    return fake_chat


def test_valid_response_is_parsed(monkeypatch):
    content = json.dumps({
        "invoice_type": "electricity",
        "fuel_type": None,
        "supplier": "Green Power Ltd",
        "period_start": "2025-03-01",
        "period_end": "2025-03-31",
        "quantity": 500,
        "unit": "kWh",
        "total_amount": 150.0,
        "currency": "EUR",
    })
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
    content = json.dumps({"period_start": "March 2025", "period_end": "2025-03-31"})
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert fields["period_start"] is None
    assert fields["period_end"] == "2025-03-31"


def test_null_values_stay_none(monkeypatch):
    content = json.dumps({"invoice_type": "fuel", "quantity": None})
    monkeypatch.setattr(llm, "chat", fake_chat_returning(content))
    fields = llm.extract_with_llm("any text")
    assert fields["invoice_type"] == "fuel"
    assert fields["quantity"] is None
