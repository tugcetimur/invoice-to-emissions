# UK sample invoices: hand-checked findings

Nine synthetic invoices (`data/uk_samples`, see the note in that folder) with the layouts of UK business energy and fuel bills. They were used to look at the one-sheet workbook tool (v1.1) and are now a development set. They are used up as evidence: any accuracy claim after changing the readers needs a new unseen set.

## What one run showed (31 Oct 2026)
- 9 PDFs: emission confirmed for 0, human review for 9. The regex reader found no invoice type or consumption on any of them, so the invoice type was confirmed by one reader (the LLM) only.
- No wrong number was approved. An indicative value (unconfirmed, in its own column) is shown for 2 invoices (4 and 6, 6.605 tCO2e in total) and both match the PDFs.
- Before the quantity rule was added to the indicative value, the same run showed 53.978 tCO2e for five invoices (1, 2, 4, 6, 8). The correct value for those five is 14.31 tCO2e (location-based). The rule was added after checking invoices 1 and 2 against the PDFs.

## Hand check (LLM values against the PDFs)
| Invoice | Wrong or missing | Caught by the system |
|---|---|---|
| 1 British Energy | Quantity 56,640 kWh. The consumption is 15,220 kWh (day 11,720 + night 3,500, also on the CCL line). 56,840 is a meter end reading | Yes: the number is not in the text |
| 2 Octopus | Quantity 112,400 kWh is the meter start reading; the consumption is 18,500 kWh. total_amount 5,540 instead of 5,550 | Partly: the price check could not run |
| 3 Shell | Only the diesel line (620.5 L, 749.78 GBP) was read. The E10 line (120 L, 149.95 GBP) is missing. Amount due 1,079.68 GBP | No: one quantity per invoice, and the price check passes on the first line |
| 4 British Gas | Nothing wrong | Indicative value shown, correct |
| 5 BP | total_amount is the net amount (2,175.00 GBP), the amount payable is 2,610.00 GBP. The product check did not confirm diesel although the text says "Commercial Diesel (EN590 Grade)" | No |
| 6 EDF | Nothing wrong | Indicative value shown, correct |
| 7 Calor | Category natural gas, the product is LPG. The period 10-24 Mar is the invoice date to the due date; the delivery date is 9 Mar | Category: yes (the unit does not fit). Period: no |
| 8 E.ON | Quantity 98,600 kWh is not in the text. The consumption is 9,800 kWh (the meter reading starts at 98,200) | Yes: the number is not in the text |
| 9 Crown Oil | The product is kerosene heating oil, read as petrol. The period 15-29 May is the invoice date to the due date; the delivery date is 14 May | Category: yes (the product check did not confirm petrol). Period: no |

## Answer key (hand-computed, to be re-checked before any measurement)
| Invoice | Consumption | Factor (kgCO2e) | kgCO2e |
|---|---|---|---|
| 1 | 15,220 kWh electricity | 0.177 per kWh | 2,693.94 |
| 2 | 18,500 kWh green electricity (renewable tariff) | market-based 0 (location-based 0.177 would give 3,274.50) | 0 (3,274.50 location-based) |
| 3 | 620.5 L diesel and 120 L petrol (E10) | 2.57082 and 2.06916 per litre | 1,595.19 + 248.30 = 1,843.49 |
| 4 | 1,115 m3 natural gas (12,400 kWh on the bill) | 2.06672 per m3 | 2,304.39 (2,268.70 with the kWh factor) |
| 5 | 1,450 L diesel | 2.57082 per litre | 3,727.69 |
| 6 | 24,300 kWh electricity | 0.177 per kWh | 4,301.10 |
| 7 | 850 L LPG | no factor in the table | not computable yet |
| 8 | 9,800 kWh electricity | 0.177 per kWh | 1,734.60 |
| 9 | 2,000 L kerosene heating oil | no factor in the table | not computable yet |

## Findings for v2
1. Meter readings are read as consumption (invoices 1, 2 and 8).
2. Several products on one invoice (3); the data model holds one quantity per invoice.
3. The billing period can be invented from the invoice and due dates (7, 9); only its presence is checked.
4. total_amount is sometimes the amount payable, sometimes the net amount, sometimes one line (2, 3, 5).
5. No factors for LPG and kerosene, and no way to say "green electricity". Decision: add a green electricity category with a market-based factor of 0 and show the location-based value next to it (the GHG Protocol Scope 2 guidance asks for both).
6. Consistency rules seen on these nine only, so a lead and not a rule: the consumption lines add up to the CCL line kWh (invoices 1, 2, 4, 6, 8) and the line amounts add up to the net total (invoice 3: 749.78 + 149.95 = 899.73).
7. Gas billed in m3 and kWh (4): the two factors differ by about 1.6 %.
8. The regex reader does not know these layouts, so no invoice type is confirmed by two readers.
