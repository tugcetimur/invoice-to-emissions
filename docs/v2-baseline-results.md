# v2 baseline results (dev set, v1.1.0 code)

Run on 7 November 2026 with the v1.1.0 code on `main` (0768c75), after the predictions were committed.
Command: `python -m scripts.make_footprint_excel --pdf-dir data/uk_electricity/dev --out output/dev_baseline.xlsx`
Set: `data/uk_electricity/dev/` (12 invoices, 5 layouts). Answer key: `tests/ground_truth_uk_electricity_dev.csv`.
This is the development set, not the official test.

## Headline

- Emission confirmed by the pipeline: **0 of 12**. All 12 went to human review.
- Every invoice has the same first reason: `invoice_type: llm_only (regex=None, llm='electricity')`.
  The regex reader does not recognise these invoices as electricity, so the two readers can never agree on the type.
- Indicative quantity matches the answer key: **6 of 12**, all in layout L5.
- No silent error: the 3 wrong quantities were caught by the price plausibility check, and the other 3 were empty.

## Per invoice

| ID | Layout | Key (kWh) | Read (kWh) | Match | Outcome |
|---|---|---|---|---|---|
| D-01 | L1 | 460 | 12,450 | no | review, implausible price per unit |
| D-02 | L1 | 480 | 15,400 | no | review, implausible price per unit |
| D-03 | L1 | 440 | 7,680 | no | review, implausible price per unit |
| D-04 | L2 | 370 | empty | no | review, quantity empty |
| D-05 | L3 | 2,270 | empty | no | review, quantity empty |
| D-06 | L4 | 280 | empty | no | review, quantity empty |
| D-07 | L5 | 263.1 | 263.1 | yes | review (invoice type only) |
| D-08 | L5 | 330.5 | 330.5 | yes | review (invoice type only) |
| D-09 | L5 | 176.9 | 176.9 | yes | review (invoice type only) |
| D-10 | L5 | 286.4 | 286.4 | yes | review (invoice type only) |
| D-11 | L5 | 241.8 | 241.8 | yes | review (invoice type only) |
| D-12 | L5 | 164.8 | 164.8 | yes | review (invoice type only) |

## Per layout (correct quantity)

- L1 (3 invoices): 0
- L2 (1): 0
- L3 (1): 0
- L4 (1): 0
- L5 (6): 6

## Predictions versus result

Predicted correct: D-01, D-02, D-03 (3 of 12). Actual correct: D-07 to D-12 (6 of 12).
Per invoice, the prediction was right for 3 of 12 (D-04, D-05, D-06).
The prediction was reversed for L1 and L5: the simple tables failed and the domestic statements,
where a meter-reading mix-up was expected, were read correctly.

## What this tells us (for v2)

1. Invoice type recognition in the regex reader is the first problem: it blocks all 12 from being confirmed.
2. For L1 the quantity comes from the local model only (regex found nothing) and it is far off. The cause is not yet checked.
3. Multi-line invoices (L2, L3) and the solar invoice (L4) give no quantity at all.
4. The safety design held on this set: nothing wrong was confirmed.
