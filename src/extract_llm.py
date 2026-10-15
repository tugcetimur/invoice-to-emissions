import os
from datetime import date
from typing import Literal, Optional

from ollama import chat
from pydantic import BaseModel, ValidationError

from src.extract_rules import FIELDS, read_pdf_text

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

SYSTEM_PROMPT = """You extract data from utility and fuel invoices.
Return only the requested JSON fields.

Rules:
- If a value is not clearly stated in the invoice text, return null. Never guess.
- invoice_type is one of: electricity, natural_gas, fuel.
- fuel_type is diesel or petrol for fuel invoices, otherwise null.
- Dates must be in ISO format YYYY-MM-DD.
- quantity and total_amount must be plain numbers without thousands separators or currency symbols.
- quantity is the amount consumed in the billing period, not a meter reading.
- unit is one of: kWh, MWh, m3, litre.
- currency is a three-letter code such as EUR.
- supplier is the name of the company that issued the invoice."""


class LLMInvoice(BaseModel):
    invoice_type: Optional[Literal["electricity", "natural_gas", "fuel"]] = None
    fuel_type: Optional[Literal["diesel", "petrol"]] = None
    supplier: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[Literal["kWh", "MWh", "m3", "litre"]] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None


def valid_iso_date(value):
    """Return the value as an ISO date string, or None if it is not a valid date."""
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return None


def extract_with_llm(text, model=None):
    """Ask the local model to extract invoice fields from the text."""
    empty = {name: None for name in FIELDS}

    response = chat(
        model=model or MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Invoice text:\n\n{text}"},
        ],
        format=LLMInvoice.model_json_schema(),
        options={"temperature": 0},
    )

    try:
        parsed = LLMInvoice.model_validate_json(response.message.content)
    except ValidationError:
        return empty

    fields = parsed.model_dump()
    fields["period_start"] = valid_iso_date(fields["period_start"])
    fields["period_end"] = valid_iso_date(fields["period_end"])
    return {name: fields[name] for name in FIELDS}


def extract_from_pdf(path):
    """Full local-LLM path: PDF file -> dictionary of fields."""
    return extract_with_llm(read_pdf_text(path))
