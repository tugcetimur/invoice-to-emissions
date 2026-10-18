# Final exam: local LLM on the messy set

Written and committed BEFORE running the LLM on the messy set.
Model: llama3.2:3b, prompt and code as of experiment 3. The messy set is evaluated once.

## Rules
1. One official run. No prompt or code changes after seeing the results.
2. Report the results whatever they are.
3. After this run the messy set is no longer a clean test set. A new unseen set is needed for any later claim.

## Predictions (written before the run)
- Invoices fully correct: 1 to 4 out of 13
- Invoices with all critical fields correct: 8 to 11 out of 13
- Invoices with a silently wrong critical field: 1 to 3
- INV-M-05 and INV-M-11: period dates will be missed (full month names or month only; our date parser does not know these formats)
- Number formats are the main silent risk: INV-M-03 (1.234,5 and 1.287,60) and INV-M-12 (98,40)
- INV-M-07 (Gasoil, supplier RoadStar Petrol) is a risk for the fuel type, but not independent evidence because the supplier trap was seen on the standard set
- Labels the regex missed (INV-M-01, 02, 04, 10) should mostly be read correctly by the model
- Time: about 4 seconds per invoice

## Results (official run, 18 Oct 2026)
| | Regex | LLM |
|---|---|---|
| Fully correct invoices | 1/13 | 9/13 |
| Critical fields correct | 5/13 | 11/13 |
| Invoices with a silent critical error | 1 | 2 |
| Missed cells / wrong cells | 25 / 3 | 4 / 2 |
| Seconds per invoice | ~0 | 3.6 |

Silent critical errors of the LLM:
- INV-M-02: quantity 842000 instead of 842 (unit written as KWH). Emission would be 1000 times too high.
- INV-M-07: fuel type petrol instead of diesel (product "Gasoil", supplier "RoadStar Petrol"). Emission about 20 percent too low.

Missed by the LLM pipeline: period dates of INV-M-05 and INV-M-11. The model most likely copied them, our date parser does not know these formats (full month names, month only).

## Prediction scorecard
6 of 8 predictions held. Missed: the number of fully correct invoices was underestimated (predicted 1 to 4, actual 9) and the number formats (INV-M-03, INV-M-12) were read correctly, while the real silent risks were INV-M-02 and INV-M-07.

## Status
The messy set is now burned for tuning. Any later claim needs a new unseen set.
