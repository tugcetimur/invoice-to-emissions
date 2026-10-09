from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

ALLOWED_UNITS = {
    "electricity": {"kWh", "MWh"},
    "natural_gas": {"m3", "kWh"},
    "fuel": {"litre"},
}


class InvoiceData(BaseModel):
    invoice_type: Literal["electricity", "natural_gas", "fuel"]
    fuel_type: Optional[Literal["diesel", "petrol"]] = None
    supplier: Optional[str] = None
    period_start: date
    period_end: date
    quantity: float = Field(gt=0)
    unit: Literal["kWh", "MWh", "m3", "litre"]
    total_amount: Optional[float] = None
    currency: Optional[str] = None

    @model_validator(mode="after")
    def check_consistency(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end is before period_start")
        if self.unit not in ALLOWED_UNITS[self.invoice_type]:
            raise ValueError(
                f"unit {self.unit} is not valid for {self.invoice_type}"
            )
        if self.invoice_type == "fuel" and self.fuel_type is None:
            raise ValueError("fuel invoices need a fuel_type")
        if self.invoice_type != "fuel" and self.fuel_type is not None:
            raise ValueError("fuel_type is only valid for fuel invoices")
        return self
