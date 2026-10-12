import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT_DIR = Path("data/messy_invoices")
TRUTH_PATH = Path("tests/ground_truth_messy.csv")

FIELDS = [
    "invoice_id", "file_name", "invoice_type", "fuel_type", "supplier",
    "period_start", "period_end", "quantity", "unit", "total_amount",
    "currency", "twist",
]


def record(n, twist, invoice_type, fuel_type, supplier, start, end,
           quantity, unit, total, currency, lines):
    invoice_id = f"INV-M-{n:02d}"
    return {
        "invoice_id": invoice_id,
        "file_name": f"{invoice_id}.pdf",
        "invoice_type": invoice_type,
        "fuel_type": fuel_type,
        "supplier": supplier,
        "period_start": start,
        "period_end": end,
        "quantity": quantity,
        "unit": unit,
        "total_amount": total,
        "currency": currency,
        "twist": twist,
        "lines": lines,
    }


INVOICES = [
    record(1, "unfamiliar quantity label", "electricity", None, "Green Power Ltd",
           "2025-03-01", "2025-03-31", 500, "kWh", 150.00, "EUR", [
        "Green Power Ltd",
        "Invoice no: M-01",
        "Description: Electricity supply",
        "Billing period: 01 Mar 2025 - 31 Mar 2025",
        "Energy used this month: 500 kWh",
        "Total due: EUR 150.00",
    ]),
    record(2, "unit written in capitals", "electricity", None, "BrightGrid Power",
           "2025-04-01", "2025-04-30", 842, "kWh", 210.50, "EUR", [
        "BrightGrid Power",
        "Invoice no: M-02",
        "Description: Electricity supply",
        "Statement period: 2025-04-01 - 2025-04-30",
        "Usage: 842 KWH",
        "Amount payable: EUR 210.50",
    ]),
    record(3, "European number format", "electricity", None, "Solaris Utility",
           "2025-03-01", "2025-03-31", 1234.5, "kWh", 1287.60, "EUR", [
        "Solaris Utility",
        "Invoice no: M-03",
        "Description: Electricity supply",
        "Billing period: 01 Mar 2025 - 31 Mar 2025",
        "Consumption: 1.234,5 kWh",
        "Total due: EUR 1.287,60",
    ]),
    record(4, "cubic metre sign (m3 with superscript)", "natural_gas", None,
           "Metro Gas Co", "2025-02-01", "2025-02-28", 312, "m3", 245.80, "EUR", [
        "Metro Gas Co",
        "Invoice no: M-04",
        "Description: Natural gas supply",
        "Service dates: 01/02/2025 - 28/02/2025",
        "Quantity used: 312 m\u00b3",
        "Total (incl. VAT): EUR 245.80",
    ]),
    record(5, "dates written with 'to' and full month names", "natural_gas", None,
           "BlueFlame Gas", "2025-03-01", "2025-03-31", 450, "kWh", 120.00, "EUR", [
        "BlueFlame Gas",
        "Invoice no: M-05",
        "Description: Natural gas supply",
        "Billing period: 1 March 2025 to 31 March 2025",
        "Consumption: 450 kWh",
        "Total due: EUR 120.00",
    ]),
    record(6, "unknown petrol name (ULP 95)", "fuel", "petrol", "Apex Fuels",
           "2025-05-01", "2025-05-31", 640, "litre", 1180.40, "EUR", [
        "Apex Fuels",
        "Invoice no: M-06",
        "Description: ULP 95",
        "Statement period: 2025-05-01 - 2025-05-31",
        "Usage: 640 litre",
        "Amount payable: EUR 1180.40",
    ]),
    record(7, "unknown diesel name (Gasoil)", "fuel", "diesel", "RoadStar Petrol",
           "2025-06-01", "2025-06-30", 900, "litre", 1570.00, "EUR", [
        "RoadStar Petrol",
        "Invoice no: M-07",
        "Description: Gasoil (B7)",
        "Billing period: 01 Jun 2025 - 30 Jun 2025",
        "Consumption: 900 litre",
        "Total due: EUR 1570.00",
    ]),
    record(8, "currency written after the amount", "electricity", None,
           "Northwind Energy", "2025-07-01", "2025-07-31", 3200, "kWh", 1250.00,
           "EUR", [
        "Northwind Energy",
        "Invoice no: M-08",
        "Description: Electricity supply",
        "Billing period: 01 Jul 2025 - 31 Jul 2025",
        "Consumption: 3,200 kWh",
        "Total due: 1,250.00 EUR",
    ]),
    record(9, "supplier name is not the first line", "electricity", None,
           "SunRise Electricity", "2025-08-01", "2025-08-31", 2150, "kWh", 560.25,
           "EUR", [
        "INVOICE",
        "SunRise Electricity",
        "Invoice no: M-09",
        "Description: Electricity supply",
        "Billing period: 01 Aug 2025 - 31 Aug 2025",
        "Consumption: 2,150 kWh",
        "Total due: EUR 560.25",
    ]),
    record(10, "earlier line with a similar label (last year usage)", "electricity",
           None, "BrightGrid Power", "2025-09-01", "2025-09-30", 520, "kWh", 111.80,
           "EUR", [
        "BrightGrid Power",
        "Invoice no: M-10",
        "Description: Electricity supply",
        "Customer no: 4471920",
        "Tariff: 0.2150 EUR/kWh",
        "Last year's Usage: 4,100 kWh",
        "Billing period: 01 Sep 2025 - 30 Sep 2025",
        "Consumption: 520 kWh",
        "Total due: EUR 111.80",
    ]),
    record(11, "period given as a month only", "natural_gas", None, "Metro Gas Co",
           "2025-10-01", "2025-10-31", 275, "m3", 98.50, "EUR", [
        "Metro Gas Co",
        "Invoice no: M-11",
        "Description: Natural gas supply",
        "Billing period: October 2025",
        "Consumption: 275 m3",
        "Total due: EUR 98.50",
    ]),
    record(12, "Portuguese language invoice", "electricity", None, "Luz do Sul Lda",
           "2025-03-01", "2025-03-31", 380, "kWh", 98.40, "EUR", [
        "Luz do Sul Lda",
        "Fatura no: M-12",
        "Descri\u00e7\u00e3o: Fornecimento de eletricidade",
        "Per\u00edodo: 01/03/2025 - 31/03/2025",
        "Consumo: 380 kWh",
        "Total a pagar: 98,40 EUR",
    ]),
    record(13, "control invoice (standard format)", "electricity", None,
           "Northwind Energy", "2025-11-01", "2025-11-30", 1800, "kWh", 420.00,
           "EUR", [
        "Northwind Energy",
        "Invoice no: M-13",
        "Description: Electricity supply",
        "Billing period: 01 Nov 2025 - 30 Nov 2025",
        "Consumption: 1,800 kWh",
        "Total due: EUR 420.00",
    ]),
]


def draw_invoice(path, lines):
    c = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, lines[0])
    y -= 40
    c.setFont("Helvetica", 11)
    for line in lines[1:]:
        c.drawString(50, y, line)
        y -= 22
    c.save()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    for rec in INVOICES:
        draw_invoice(OUT_DIR / rec["file_name"], rec["lines"])

    with open(TRUTH_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(INVOICES)

    print(f"{len(INVOICES)} messy invoices written to {OUT_DIR}")


if __name__ == "__main__":
    main()
