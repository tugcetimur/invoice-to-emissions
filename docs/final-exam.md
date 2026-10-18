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
