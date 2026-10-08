import calendar
import csv
import random
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

random.seed(42)  # her çalıştırmada aynı sonucu verir

OUT_DIR = Path("data/sample_invoices")
TRUTH_PATH = Path("tests/ground_truth.csv")

FIELDS = [
    "invoice_id", "file_name", "invoice_type", "fuel_type", "supplier",
    "period_start", "period_end", "quantity", "unit",
    "total_amount", "currency", "layout_id",
]

SUPPLIERS = {
    "electricity": ["Northwind Energy", "BrightGrid Power", "Solaris Utility"],
    "natural_gas": ["BlueFlame Gas", "Metro Gas Co"],
    "fuel": ["Apex Fuels", "RoadStar Petrol"],
}

SPECS = {
    "electricity": {"units": ["kWh", "MWh"], "price": (0.10, 0.35)},
    "natural_gas": {"units": ["m3", "kWh"], "price": (0.05, 1.10)},
    "fuel": {"units": ["litre"], "price": (1.40, 2.10)},
}

DESCRIPTIONS = {
    "electricity": "Electricity supply",
    "natural_gas": "Natural gas supply",
}

FUEL_NAMES = {
    1: {"diesel": "Diesel", "petrol": "Petrol"},
    2: {"diesel": "Diesel B7", "petrol": "Unleaded 95"},
    3: {"diesel": "Automotive diesel", "petrol": "Unleaded petrol"},
}

DATE_FORMATS = {1: "%d %b %Y", 2: "%Y-%m-%d", 3: "%d/%m/%Y"}
LABELS = {
    1: {"period": "Billing period", "qty": "Consumption", "total": "Total due"},
    2: {"period": "Statement period", "qty": "Usage", "total": "Amount payable"},
    3: {"period": "Service dates", "qty": "Quantity used", "total": "Total (incl. VAT)"},
}


def random_quantity(unit):
    if unit == "MWh":
        return round(random.uniform(3, 40), 1)
    if unit == "kWh":
        return random.randint(200, 5000)
    if unit == "m3":
        return random.randint(50, 900)
    return random.randint(40, 1500)  # litre


def random_period():
    month = random.randint(1, 12)
    last_day = calendar.monthrange(2025, month)[1]
    return date(2025, month, 1), date(2025, month, last_day)


def make_record(i, invoice_type):
    spec = SPECS[invoice_type]
    unit = random.choice(spec["units"])
    quantity = random_quantity(unit)
    unit_price = random.uniform(*spec["price"])
    if unit == "MWh":
        unit_price *= 1000  # fiyat MWh başına
    start, end = random_period()
    invoice_id = f"INV-2025-{i:03d}"
    fuel_type = random.choice(["diesel", "petrol"]) if invoice_type == "fuel" else ""
    return {
        "invoice_id": invoice_id,
        "file_name": f"{invoice_id}.pdf",
        "invoice_type": invoice_type,
        "fuel_type": fuel_type,
        "supplier": random.choice(SUPPLIERS[invoice_type]),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "quantity": quantity,
        "unit": unit,
        "total_amount": round(quantity * unit_price, 2),
        "currency": "EUR",
        "layout_id": random.randint(1, 3),
    }


def draw_invoice(path, rec):
    layout = rec["layout_id"]
    labels = LABELS[layout]
    fmt = DATE_FORMATS[layout]
    start = date.fromisoformat(rec["period_start"]).strftime(fmt)
    end = date.fromisoformat(rec["period_end"]).strftime(fmt)
    qty = rec["quantity"]
    qty_text = f"{qty:,}" if layout == 1 else str(qty)

    if rec["invoice_type"] == "fuel":
        description = FUEL_NAMES[layout][rec["fuel_type"]]
    else:
        description = DESCRIPTIONS[rec["invoice_type"]]

    lines = [
        f"Invoice no: {rec['invoice_id']}",
        f"Description: {description}",
        f"{labels['period']}: {start} - {end}",
    ]
    # Layout 3 kafa karıştırıcı: sayaç okumaları da yazılı
    if layout == 3 and rec["invoice_type"] != "fuel":
        previous = random.randint(1000, 90000)
        lines.append(f"Previous reading: {previous}")
        lines.append(f"Current reading: {round(previous + qty, 1)}")
    lines.append(f"{labels['qty']}: {qty_text} {rec['unit']}")
    if layout == 3:
        net = round(rec["total_amount"] / 1.2, 2)
        vat = round(rec["total_amount"] - net, 2)
        lines.append(f"Amount excl. VAT: {rec['currency']} {net:.2f}")
        lines.append(f"VAT 20%: {rec['currency']} {vat:.2f}")
    lines.append(f"{labels['total']}: {rec['currency']} {rec['total_amount']:.2f}")

    c = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, rec["supplier"])
    y -= 40
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(50, y, line)
        y -= 22
    c.save()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    plan = ["electricity"] * 6 + ["natural_gas"] * 5 + ["fuel"] * 5
    records = []
    for i, invoice_type in enumerate(plan, start=1):
        rec = make_record(i, invoice_type)
        draw_invoice(OUT_DIR / rec["file_name"], rec)
        records.append(rec)

    with open(TRUTH_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"{len(records)} invoices written to {OUT_DIR}")


if __name__ == "__main__":
    main()
