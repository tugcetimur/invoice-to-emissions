# v2 baseline predictions (dev set, v1.1.0 code)

Written by Tugce on 7 November 2026, before the baseline was run.
Set: `data/uk_electricity/dev/` (12 invoices). Answer key: `tests/ground_truth_uk_electricity_dev.csv`.

"Correct" means the location-based emission of the invoice matches the answer key.
This is a development set, not the official test. The prediction measures our intuition about
the v1.1.0 code; it is not a score.

| ID | Layout | Prediction | Why |
|---|---|---|---|
| D-01 | L1 | Correct | Simple table, one kWh line |
| D-02 | L1 | Correct | Simple table, one kWh line |
| D-03 | L1 | Correct | Simple table, one kWh line |
| D-04 | L2 | Wrong | Day and night lines have to be added up |
| D-05 | L3 | Wrong | Day and night lines have to be added up |
| D-06 | L4 | Wrong | Solar: import and export both appear |
| D-07 | L5 | Wrong | The code may read the current meter reading as consumption |
| D-08 | L5 | Wrong | Same |
| D-09 | L5 | Wrong | Same |
| D-10 | L5 | Wrong | Same |
| D-11 | L5 | Wrong | Same |
| D-12 | L5 | Wrong | Same |

Expected correct: 3 of 12.

By layout (expected correct):
- L1 (3 invoices): 3
- L2 (1): 0
- L3 (1): 0
- L4 (1): 0
- L5 (6): 0

Invoice most likely to be wrong without being flagged for review:
invoices with two or more usage lines (D-04, D-05). The regex may not add them up.
The local model (Ollama) may read them, but I am not sure it can add numbers.
