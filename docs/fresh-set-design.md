# Fresh evaluation set: design

Written and committed BEFORE the invoices are generated and BEFORE the pipeline is run on them.

## Purpose
Measure the full pipeline (regex reader, local LLM reader, hybrid merge, checks, policy, period check, duplicate check) on invoices it has never seen.

## Rules
1. The design and the ideal outcomes below are fixed once committed.
2. Predictions are written and committed before the run.
3. One official run. No rule, prompt or code change after seeing the results.
4. Report the results whatever they are. Gaps found go to docs/real-world-risks.md, not into this run.
5. After the run this set is used up; a new claim needs a new unseen set.

## Outcome measures (per invoice)
- Processed correctly: processed automatically and every critical value is right.
- Silent error: processed automatically with a wrong critical value, or processed although it should have gone to review. Target: zero.
- Needed review: sent to a human and it should have been.
- Unneeded review: sent to a human although it could have been processed.
- Deviation in total emissions: automatically processed invoices versus the ground truth.

## Invoices (25)
| ID | Twist | Ideal outcome |
|---|---|---|
| F-01 to F-06 | Controls with new suppliers and values: electricity kWh, electricity MWh, gas m3, gas kWh, fuel diesel, fuel petrol | process |
| F-07 | Unit written out: kilowatt-hours | process |
| F-08 | New label: Energy used | process |
| F-09 | Space as thousands separator: 1 234 kWh | process |
| F-10 | Currency symbol before the amount: EUR sign 98.40 | process |
| F-11 | Period written as 2025-03-01 to 2025-03-31 | process |
| F-12 | Premium unleaded 98 and unit L | process |
| F-13 | Euro diesel B7 and decimal comma: 1.250,5 litres | process |
| F-14 | Header line (TAX INVOICE) before the supplier name | process |
| F-15 | Gas label without the word natural: Gas supply | process |
| F-16 | Quantity not written anywhere (information really missing) | review |
| F-17 | Period given as a month name only: October 2025 | review |
| F-18 | Heating oil (separate factor in factor tables) | review |
| F-19 | Credit note with a negative quantity: -120 kWh | review |
| F-20 | Same content as F-01 under another file name | first copy processed, duplicate reviewed |
| F-21 | Gas in MWh (the schema accepts only m3 and kWh for gas) | review |
| F-22 | Turkish-language invoice: Tuketim: 540 kWh | process (hard) |
| F-23 | Active 840 kWh next to a reactive 120 kVArh line | process (hard) |
| F-24 | Day 300 kWh and night 200 kWh tariff lines, total 500 | process or review (hard) |
| F-25 | 1.2 MWh (1200 kWh) written together | process or review (hard) |

## Not in scope for this run
Rules for the problems listed in docs/real-world-risks.md. This run measures the current system; it does not tune it.
