from pathlib import Path

import pandas as pd

from src.schema import InvoiceData

FACTORS_PATH = Path("data/emission_factors.csv")

# Invoice type -> value of "energy_or_fuel" in the factor table
ENERGY_KEYS = {
    "electricity": "grid_electricity",
    "natural_gas": "natural_gas",
}


def load_factors(path=FACTORS_PATH):
    """Read the emission factor table into a DataFrame."""
    return pd.read_csv(path)


def to_factor_unit(quantity, unit):
    """Convert to the unit used in the factor table (MWh -> kWh)."""
    if unit == "MWh":
        return quantity * 1000, "kWh"
    return quantity, unit


def find_factor(invoice: InvoiceData, factors: pd.DataFrame) -> dict:
    """Find the single factor row that matches the invoice."""
    _, unit = to_factor_unit(invoice.quantity, invoice.unit)

    if invoice.invoice_type == "fuel":
        energy = invoice.fuel_type
    else:
        energy = ENERGY_KEYS[invoice.invoice_type]

    mask = (
        (factors["activity_type"] == invoice.invoice_type)
        & (factors["energy_or_fuel"] == energy)
        & (factors["unit"] == unit)
    )
    matches = factors[mask]

    if len(matches) == 0:
        raise ValueError(f"No factor found for {invoice.invoice_type}/{energy}/{unit}")
    if len(matches) > 1:
        raise ValueError(f"Multiple factors found for {invoice.invoice_type}/{energy}/{unit}")
    return matches.iloc[0].to_dict()
