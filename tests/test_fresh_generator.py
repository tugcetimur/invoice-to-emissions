from scripts.generate_fresh_invoices import INVOICES
from src.validate import is_grounded

SKIP_QUANTITY = {"F-09", "F-16", "F-19", "F-24"}
SKIP_TOTAL = {"F-19"}


def test_the_numbers_in_the_ground_truth_appear_in_the_invoice_text():
    for rec in INVOICES:
        text = "\n".join(rec["lines"])
        if rec["invoice_id"] not in SKIP_QUANTITY and rec["quantity"] is not None:
            assert is_grounded(rec["quantity"], text), rec["invoice_id"]
        if rec["invoice_id"] not in SKIP_TOTAL:
            assert is_grounded(rec["total_amount"], text), rec["invoice_id"]
