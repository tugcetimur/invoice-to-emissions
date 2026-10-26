import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT_DIR = Path("data/fresh_invoices")
TRUTH_PATH = Path("tests/ground_truth_fresh.csv")

FIELDS = [
    "invoice_id", "file_name", "invoice_type", "fuel_type", "supplier",
    "period_start", "period_end", "quantity", "unit", "total_amount",
    "currency", "expected_outcome", "twist",
]


def record(n, twist, expected, invoice_type, fuel_type, supplier, start, end,
           quantity, unit, total, currency, lines):
    invoice_id = f"F-{n:02d}"
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
        "expected_outcome": expected,
        "twist": twist,
        "lines": lines,
    }


def standard(n, supplier, description, period, quantity_line, total_line):
    """The usual layout: supplier, invoice number, description, period, quantity, total."""
    return [
        supplier,
        f"Invoice no: F-{n:02d}",
        f"Description: {description}",
        f"Billing period: {period}",
        quantity_line,
        total_line,
    ]


F01_LINES = standard(1, "Aurora Power", "Electricity supply", "01 Jan 2025 - 31 Jan 2025",
                     "Consumption: 620 kWh", "Total due: EUR 161.20")

INVOICES = [
    record(1, "control: electricity kWh", "process", "electricity", None, "Aurora Power",
           "2025-01-01", "2025-01-31", 620, "kWh", 161.20, "EUR", F01_LINES),
    record(2, "control: electricity MWh", "process", "electricity", None, "Helios Energy",
           "2025-02-01", "2025-02-28", 2.5, "MWh", 625.00, "EUR",
           standard(2, "Helios Energy", "Electricity supply", "01 Feb 2025 - 28 Feb 2025",
                    "Consumption: 2.5 MWh", "Total due: EUR 625.00")),
    record(3, "control: gas m3", "process", "natural_gas", None, "Terra Gas",
           "2025-03-01", "2025-03-31", 410, "m3", 389.50, "EUR",
           standard(3, "Terra Gas", "Natural gas supply", "01 Mar 2025 - 31 Mar 2025",
                    "Consumption: 410 m3", "Total due: EUR 389.50")),
    record(4, "control: gas kWh", "process", "natural_gas", None, "Flame Energy",
           "2025-04-01", "2025-04-30", 3800, "kWh", 342.00, "EUR",
           standard(4, "Flame Energy", "Natural gas supply", "01 Apr 2025 - 30 Apr 2025",
                    "Consumption: 3,800 kWh", "Total due: EUR 342.00")),
    record(5, "control: fuel diesel", "process", "fuel", "diesel", "Nova Fuels",
           "2025-05-01", "2025-05-31", 760, "litre", 1292.00, "EUR",
           standard(5, "Nova Fuels", "Diesel", "01 May 2025 - 31 May 2025",
                    "Consumption: 760 litre", "Total due: EUR 1292.00")),
    record(6, "control: fuel petrol", "process", "fuel", "petrol", "Meridian Fuels",
           "2025-06-01", "2025-06-30", 520, "litre", 936.00, "EUR",
           standard(6, "Meridian Fuels", "Petrol", "01 Jun 2025 - 30 Jun 2025",
                    "Consumption: 520 litre", "Total due: EUR 936.00")),
    record(7, "unit written out: kilowatt-hours", "process", "electricity", None, "Lumen Electric",
           "2025-07-01", "2025-07-31", 480, "kWh", 124.80, "EUR",
           standard(7, "Lumen Electric", "Electricity supply", "01 Jul 2025 - 31 Jul 2025",
                    "Consumption: 480 kilowatt-hours", "Total due: EUR 124.80")),
    record(8, "new label: Energy used", "process", "electricity", None, "Ember Utilities",
           "2025-08-01", "2025-08-31", 700, "kWh", 182.00, "EUR",
           standard(8, "Ember Utilities", "Electricity supply", "01 Aug 2025 - 31 Aug 2025",
                    "Energy used: 700 kWh", "Total due: EUR 182.00")),
    record(9, "space as thousands separator", "process", "electricity", None, "Delta Power",
           "2025-09-01", "2025-09-30", 1234, "kWh", 320.84, "EUR",
           standard(9, "Delta Power", "Electricity supply", "01 Sep 2025 - 30 Sep 2025",
                    "Consumption: 1 234 kWh", "Total due: EUR 320.84")),
    record(10, "currency symbol before the amount", "process", "electricity", None, "Sol Energy",
           "2025-10-01", "2025-10-31", 400, "kWh", 98.40, "EUR",
           standard(10, "Sol Energy", "Electricity supply", "01 Oct 2025 - 31 Oct 2025",
                    "Consumption: 400 kWh", "Total due: \u20ac 98.40")),
    record(11, "period written as 2025-03-01 to 2025-03-31", "process", "electricity", None, "Zenith Power",
           "2025-03-01", "2025-03-31", 560, "kWh", 145.60, "EUR",
           standard(11, "Zenith Power", "Electricity supply", "2025-03-01 to 2025-03-31",
                    "Consumption: 560 kWh", "Total due: EUR 145.60")),
    record(12, "Premium unleaded 98 and unit L", "process", "fuel", "petrol", "Orbit Fuels",
           "2025-04-01", "2025-04-30", 450, "litre", 855.00, "EUR",
           standard(12, "Orbit Fuels", "Premium unleaded 98", "01 Apr 2025 - 30 Apr 2025",
                    "Consumption: 450 L", "Total due: EUR 855.00")),
    record(13, "Euro diesel B7 and decimal comma", "process", "fuel", "diesel", "Quartz Fuels",
           "2025-05-01", "2025-05-31", 1250.5, "litre", 2125.85, "EUR",
           standard(13, "Quartz Fuels", "Euro diesel B7", "01 May 2025 - 31 May 2025",
                    "Consumption: 1.250,5 litres", "Total due: EUR 2.125,85")),
    record(14, "header line before the supplier name", "process", "electricity", None, "Orion Electricity",
           "2025-06-01", "2025-06-30", 830, "kWh", 215.80, "EUR", [
        "TAX INVOICE",
        "Orion Electricity",
        "Invoice no: F-14",
        "Description: Electricity supply",
        "Billing period: 01 Jun 2025 - 30 Jun 2025",
        "Consumption: 830 kWh",
        "Total due: EUR 215.80",
    ]),
    record(15, "gas label without the word natural", "process", "natural_gas", None, "Blue Horizon Gas",
           "2025-07-01", "2025-07-31", 2900, "kWh", 261.00, "EUR",
           standard(15, "Blue Horizon Gas", "Gas supply", "01 Jul 2025 - 31 Jul 2025",
                    "Consumption: 2,900 kWh", "Total due: EUR 261.00")),
    record(16, "quantity not written anywhere", "review", "electricity", None, "Pioneer Energy",
           "2025-08-01", "2025-08-31", None, None, 190.00, "EUR", [
        "Pioneer Energy",
        "Invoice no: F-16",
        "Description: Electricity supply",
        "Billing period: 01 Aug 2025 - 31 Aug 2025",
        "Total due: EUR 190.00",
    ]),
    record(17, "period given as a month name only", "review", "natural_gas", None, "Harbor Gas",
           "2025-10-01", "2025-10-31", 300, "m3", 285.00, "EUR",
           standard(17, "Harbor Gas", "Natural gas supply", "October 2025",
                    "Consumption: 300 m3", "Total due: EUR 285.00")),
    record(18, "heating oil", "review", "fuel", None, "Northern Oil",
           "2025-02-01", "2025-02-28", 800, "litre", 760.00, "EUR",
           standard(18, "Northern Oil", "Heating oil", "01 Feb 2025 - 28 Feb 2025",
                    "Consumption: 800 litre", "Total due: EUR 760.00")),
    record(19, "credit note with a negative quantity", "review", "electricity", None, "Aurora Power",
           "2025-01-01", "2025-01-31", -120, "kWh", -31.20, "EUR", [
        "Aurora Power",
        "Invoice no: F-19",
        "Description: Credit note, electricity supply",
        "Billing period: 01 Jan 2025 - 31 Jan 2025",
        "Consumption: -120 kWh",
        "Total due: EUR -31.20",
    ]),
    record(20, "same content as F-01 under another file name", "review", "electricity", None, "Aurora Power",
           "2025-01-01", "2025-01-31", 620, "kWh", 161.20, "EUR", F01_LINES),
    record(21, "gas in MWh", "review", "natural_gas", None, "Alpine Gas",
           "2025-09-01", "2025-09-30", 3.8, "MWh", 342.00, "EUR",
           standard(21, "Alpine Gas", "Natural gas supply", "01 Sep 2025 - 30 Sep 2025",
                    "Consumption: 3.8 MWh", "Total due: EUR 342.00")),
    record(22, "Turkish-language invoice (amount in EUR to isolate the language)", "process",
           "electricity", None, "Anadolu Enerji A.S.",
           "2025-03-01", "2025-03-31", 540, "kWh", 140.40, "EUR", [
        "Anadolu Enerji A.S.",
        "Fatura no: F-22",
        "T\u00fcr: Elektrik",
        "D\u00f6nem: 01/03/2025 - 31/03/2025",
        "T\u00fcketim: 540 kWh",
        "Toplam: 140,40 EUR",
    ]),
    record(23, "active kWh next to a reactive kVArh line", "process", "electricity", None, "Grid Partners",
           "2025-04-01", "2025-04-30", 840, "kWh", 218.40, "EUR", [
        "Grid Partners",
        "Invoice no: F-23",
        "Description: Electricity supply",
        "Billing period: 01 Apr 2025 - 30 Apr 2025",
        "Active energy: 840 kWh",
        "Reactive energy: 120 kVArh",
        "Total due: EUR 218.40",
    ]),
    record(24, "day and night tariff lines without a total", "either", "electricity", None, "Duo Energy",
           "2025-05-01", "2025-05-31", 500, "kWh", 130.00, "EUR", [
        "Duo Energy",
        "Invoice no: F-24",
        "Description: Electricity supply",
        "Billing period: 01 May 2025 - 31 May 2025",
        "Day tariff: 300 kWh",
        "Night tariff: 200 kWh",
        "Total due: EUR 130.00",
    ]),
    record(25, "MWh and kWh written together", "either", "electricity", None, "Prime Electric",
           "2025-06-01", "2025-06-30", 1200, "kWh", 312.00, "EUR",
           standard(25, "Prime Electric", "Electricity supply", "01 Jun 2025 - 30 Jun 2025",
                    "Consumption: 1.2 MWh (1200 kWh)", "Total due: EUR 312.00")),
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

    counts = {}
    for rec in INVOICES:
        counts[rec["expected_outcome"]] = counts.get(rec["expected_outcome"], 0) + 1
    print(f"{len(INVOICES)} fresh invoices written to {OUT_DIR}")
    print("Ideal outcomes:", counts)


if __name__ == "__main__":
    main()
