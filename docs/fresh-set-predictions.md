# Fresh set: predictions

Written and committed BEFORE the pipeline is run on the fresh set. The author's predictions were written first, the assistant's after.

Letters: P = processed automatically and correct, R = sent to review, S = processed automatically with a wrong value (silent error), ? = unsure.

## Predictions by the author
| ID | Twist | Prediction |
|---|---|---|
| F-01 to F-06 | Controls | P |
| F-07 | Unit written out: kilowatt-hours | P |
| F-08 | New label: Energy used | P |
| F-09 | Space as thousands separator: 1 234 kWh | R |
| F-10 | Currency symbol before the amount | P |
| F-11 | Period written as 2025-03-01 to 2025-03-31 | P |
| F-12 | Premium unleaded 98 and unit L | P |
| F-13 | Euro diesel B7 and decimal comma | ? |
| F-14 | Header line before the supplier name | P |
| F-15 | Gas label without the word natural | P |
| F-16 | Quantity not written anywhere | R |
| F-17 | Period given as a month name only | R |
| F-18 | Heating oil | R |
| F-19 | Credit note with a negative quantity | ? |
| F-20 | Same content as F-01 under another file name | ? |
| F-21 | Gas in MWh | R |
| F-22 | Turkish-language invoice | P |
| F-23 | Active kWh next to a reactive kVArh line | ? |
| F-24 | Day and night tariff lines | ? |
| F-25 | 1.2 MWh (1200 kWh) written together | R |

Summary derived from the table: 14 P, 6 R, 5 unsure. That means 14 to 19 invoices processed automatically and 6 to 11 sent to review. No silent error was predicted explicitly.

## Predictions by the assistant
Basis: knowledge of the code and of the earlier results (standard set, messy set, final exam, policy and pipeline runs).

| ID | Prediction | Reason |
|---|---|---|
| F-01 to F-06 | P | Standard layouts that both readers know |
| F-07 | P | The regex misses the spelled-out unit, the LLM normalises it to kWh, the number is in the text and the price is plausible |
| F-08 | P | The regex does not know the label (as with INV-M-01), the LLM reads 700, the checks pass |
| F-09 | R | The space splits 1 234 into two numbers, so 1234 is not found in the text |
| F-10 | P | The regex may miss the total, the LLM reads it and it is found in the text |
| F-11 | P | The LLM returns ISO dates and the parser accepts them |
| F-12 | P | Unleaded is a known word; the unit L may be missed by the regex but the LLM normalises it |
| F-13 | P | The LLM reads the decimal comma (it did for INV-M-03); if it misreads, the grounding check sends the invoice to review |
| F-14 | P | A wrong supplier from the regex does not matter, the supplier is not a critical field |
| F-15 | R | The regex needs the words natural gas, so the type comes from the LLM alone and must be confirmed by both readers |
| F-16 | R | Nothing to read. Risk: the LLM invents a quantity that passes the checks |
| F-17 | R | A month-only period is not parsed (as with INV-M-11) |
| F-18 | R | Unknown product, the type is not confirmed by the regex |
| F-19 | R | If the LLM keeps the minus sign it conflicts with the regex. Risk: both read 120 and the total loses its sign |
| F-20 | R | The duplicate check flags the second copy of F-01 |
| F-21 | R | MWh is not a valid unit for gas |
| F-22 | R | The labels are Turkish, the regex finds nothing and the type must be confirmed by both readers |
| F-23 | P | The LLM reads the active 840 kWh; if it picks 120 the price check rejects it |
| F-24 | S | The LLM picks one tariff line (300 or 200); the number is in the text and the price stays plausible. A correct sum of 500 would be rejected because it is not in the text |
| F-25 | P | The regex reads 1.2 MWh; the LLM agrees or conflicts; no silent error expected |

Summary: 15 P, 9 R, 1 S.
- Processed automatically: 16.
- Silent errors: 1 (F-24); possible extra ones at F-16 and F-19, so a range of 1 to 3.
- Sent to review: 9, of which 6 needed (F-16 to F-21) and 3 unneeded (F-09, F-15, F-22).
- Expected reviews caught: 6 of 6.
- Deviation in total emissions: below 1 percent. Fuel and gas invoices dominate the total, so an electricity error of this size barely moves it.
