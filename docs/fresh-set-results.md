# Fresh set: results of the official run

Run on 29 Oct 2026 from main (commit 00e20e1, which includes the evaluation script), with the local model llama3.2:3b and `python -m scripts.evaluate_fresh`. One official run. The raw output is in docs/fresh-set-run-output.txt. Design: docs/fresh-set-design.md. Predictions (committed before the run): docs/fresh-set-predictions.md.

## Numbers
| Measure | Result |
|---|---|
| Processed automatically | 14 of 25 |
| Processed correctly | 14 |
| Silent errors | 0 |
| Needed reviews | 6 (F-16 to F-21) |
| Acceptable reviews | 2 (F-24, F-25) |
| Unneeded reviews | 3 (F-09, F-15, F-22) |
| Crashes | 0 |
| Emissions of the processed invoices | system 9.945 t, ground truth 9.945 t, deviation +0.00 % |
| Coverage of the ideal total | 89.7 % |

## Per invoice
| ID | Ideal | Outcome | Why |
|---|---|---|---|
| F-01 to F-08 | process | correct | |
| F-09 | process | unneeded review | The space in 1 234 splits the number; the LLM read 1234 but it is not found in the text |
| F-10 to F-14 | process | correct | |
| F-15 | process | unneeded review | The regex does not know Gas supply; the type came from the LLM alone |
| F-16 | review | needed review | Quantity empty: the LLM did not invent one |
| F-17 | review | needed review | Billing period missing |
| F-18 | review | needed review | Type from the LLM alone (heating oil) |
| F-19 | review | needed review | The negative number -120 cannot be found in the text (accidental catch) |
| F-20 | review | needed review | Possible duplicate of F-01 |
| F-21 | review | needed review | Price per unit could not be checked (gas in MWh) |
| F-22 | process | unneeded review | Turkish labels; the type came from the LLM alone |
| F-23 | process | correct | The reactive line did not confuse the readers |
| F-24 | either | acceptable review | The LLM summed the tariffs to 500; 500 is not in the text |
| F-25 | either | acceptable review | Conflict: the regex read 1.2, the LLM read 1200 |

## Predictions against results
- Author: 18 of the 20 invoices with a definite prediction were right (F-15 and F-22 were predicted as processed). Five invoices were marked unsure. Predicted ranges: 14 to 19 processed (actual 14) and 6 to 11 reviews (actual 11). No silent error predicted, none found.
- Assistant: 23 of 25 invoices were right. F-24 was predicted as a silent error (the LLM summed the tariffs instead of picking one line) and F-25 as processed (the readers conflicted). Summary numbers predicted: 16 processed (actual 14), 1 silent error (actual 0), 9 reviews (actual 11), 3 unneeded reviews (actual 3), deviation below 1 % (actual 0.00 %).
- The assistant knew the code and the earlier results, so the comparison is not fair.

## What the result shows and what it does not
- It shows that on these 25 synthetic invoices no silent error occurred and the processed invoices add up to the ground truth.
- It does not show the behaviour on real invoices. The set is small, synthetic and was designed by someone who knew the weaknesses of the system. One run with a deterministic model. Two of the six needed reviews (F-19, F-21) happened for incidental reasons.

## Gaps found (not fixed in this run, backlog for v2)
1. The grounding check cannot match negative numbers; the credit note (F-19) was caught by accident. An explicit credit note rule is needed.
2. Space-grouped thousands (1 234) are not parsed.
3. The regex does not know Gas supply, Turkish labels or Heating oil as invoice types, so these go to review.
4. A derived value (the sum of two tariffs, F-24) fails the grounding check. An aggregation rule is needed.
5. Gas in MWh has neither a unit conversion nor a price band.
6. The evaluation script prints only the first reason of each review.

## Status
The fresh set is used up. A new claim after any change needs a new unseen set.
