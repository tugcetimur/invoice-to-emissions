from pathlib import Path

import pandas as pd

from src.calculate import calculate_emissions
from src.factors import load_factors
from src.schema import InvoiceData

TRUTH_PATH = Path("tests/ground_truth.csv")
OUTPUT_PATH = Path("output/emissions_ground_truth.csv")


def main():
    truth = pd.read_csv(TRUTH_PATH)
    factors = load_factors()
    rows = []

    for _, r in truth.iterrows():
        fuel_type = None if pd.isna(r["fuel_type"]) else r["fuel_type"]
        invoice = InvoiceData(
            invoice_type=r["invoice_type"],
            fuel_type=fuel_type,
            period_start=r["period_start"],
            period_end=r["period_end"],
            quantity=r["quantity"],
            unit=r["unit"],
        )
        result = calculate_emissions(invoice, factors)
        rows.append(
            {
                "invoice_id": r["invoice_id"],
                "invoice_type": r["invoice_type"],
                "fuel_type": fuel_type or "",
                "quantity": r["quantity"],
                "unit": r["unit"],
                "quantity_used": result.quantity,
                "unit_used": result.unit,
                "factor": result.factor,
                "scope": result.scope,
                "kg_co2e": round(result.kg_co2e, 3),
                "t_co2e": round(result.t_co2e, 6),
            }
        )

    df = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"{len(df)} invoices calculated, total {df['t_co2e'].sum():.3f} tCO2e")
    print(df.groupby("scope")["t_co2e"].sum().round(3))
    print(f"Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
