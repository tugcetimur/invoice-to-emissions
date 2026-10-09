from typing import Optional

import pandas as pd
from pydantic import BaseModel

from src.factors import find_factor, load_factors, to_factor_unit
from src.schema import InvoiceData


class EmissionResult(BaseModel):
    quantity: float  # quantity in the factor's unit
    unit: str
    factor: float
    factor_unit: str
    scope: int
    kg_co2e: float
    t_co2e: float
    source: str
    year: int


def calculate_emissions(
    invoice: InvoiceData, factors: Optional[pd.DataFrame] = None
) -> EmissionResult:
    """Calculate emissions for one invoice: quantity x emission factor."""
    if factors is None:
        factors = load_factors()

    quantity, unit = to_factor_unit(invoice.quantity, invoice.unit)
    row = find_factor(invoice, factors)

    kg_co2e = quantity * row["factor"]

    return EmissionResult(
        quantity=quantity,
        unit=unit,
        factor=row["factor"],
        factor_unit=row["factor_unit"],
        scope=int(row["scope"]),
        kg_co2e=kg_co2e,
        t_co2e=kg_co2e / 1000,
        source=row["source"],
        year=int(row["year"]),
    )
