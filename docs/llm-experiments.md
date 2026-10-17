# LLM extraction experiments

Development set: the 16 standard invoices. The messy set is the final exam and is not used for tuning.
Model: llama3.2:3b, temperature 0.

| # | Change | Fully correct | Critical fields ok | Critical WRONG | Sec/invoice |
|---|---|---|---|---|---|
| 0 | Baseline (first prompt) | 0/16 | 4/16 | 1/16 | 1.9 |
| 1 | All schema fields required but nullable | 14/16 | 15/16 | 1/16 | 3.7 |
| 2 | Prompt: decide fuel type only from the product line, never from the supplier name | 15/16 | 16/16 | 0/16 | 4.0 |
| 3 | Model copies dates as written, code converts them (day first). Side effect: INV-2025-015 supplier truncated to "RoadStar" (non-critical) | 15/16 | 16/16 | 0/16 | 3.9 |
