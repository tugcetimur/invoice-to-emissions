import sys

from src.extract_llm import extract_with_llm
from src.extract_rules import FIELDS, extract_fields, read_pdf_text
from src.hybrid import merge_fields, review_reasons
from src.products import fuel_product_check
from src.validate import is_grounded, price_is_plausible


def first(*values):
    return next((v for v in values if v is not None), None)


text = read_pdf_text(sys.argv[1])
regex_fields = extract_fields(text)
llm_fields = extract_with_llm(text)
merged = merge_fields(regex_fields, llm_fields)

print(f"{'field':14s} {'regex':22s} {'llm':22s} status")
for field in FIELDS:
    item = merged[field]
    print(f"{field:14s} {str(item['regex']):22s} {str(item['llm']):22s} {item['status']}")

reasons = review_reasons(merged)
print("\nHybrid decision:", "automatic" if not reasons else "REVIEW")
for reason in reasons:
    print("  -", reason)

invoice_type = first(merged["invoice_type"]["value"], llm_fields["invoice_type"], regex_fields["invoice_type"])
unit = first(merged["unit"]["value"], llm_fields["unit"], regex_fields["unit"])
total = first(merged["total_amount"]["value"], llm_fields["total_amount"], regex_fields["total_amount"])

print("\nChecks against the invoice itself:")
for source, fields in (("regex", regex_fields), ("llm", llm_fields)):
    quantity = fields["quantity"]
    if quantity is None:
        print(f"  {source:5s} quantity: nothing to check")
        continue
    print(
        f"  {source:5s} quantity {quantity}: in the text = {is_grounded(quantity, text)}, "
        f"price plausible = {price_is_plausible(invoice_type, unit, quantity, total)}"
    )
if invoice_type == "fuel":
    for source, fields in (("regex", regex_fields), ("llm", llm_fields)):
        fuel = fields["fuel_type"]
        if fuel is not None:
            print(f"  {source:5s} fuel type {fuel}: product line says {fuel_product_check(fuel, text)}")
