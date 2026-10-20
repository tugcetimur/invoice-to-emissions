# Hybrid decision results

Policy: auto-process an invoice only if both readers confirm every critical field (invoice type, fuel type, quantity, unit). Otherwise send it to review with reasons.

| Set | Auto-processed | Silent critical errors | Sent to review | Unneeded reviews* |
|---|---|---|---|---|
| Standard (16) | 16 | 0 | 0 | 0 |
| Messy (13), already used | 5 | 0 | 8 | 6 |

\* "Unneeded" means the LLM alone had every critical field right. It is measured with hindsight: the system cannot know it in advance, and one of these (INV-M-10) was a real conflict with the regex.

Without the hybrid: the LLM alone would have silently mis-processed 2 of 13 messy invoices (INV-M-02, INV-M-07), the regex alone 1 (INV-M-10).

## Caveats
- The messy set was already used, so its numbers are a demonstration, not independent evidence.
- INV-M-02 and INV-M-07 were caught because the regex could not confirm the LLM value, not because the wrong value was detected. A validation layer is needed for that.
- 8 of 13 reviews is too many for practical use.
