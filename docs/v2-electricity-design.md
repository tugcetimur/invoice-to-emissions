# v2 design: UK electricity invoices

Scope: UK electricity bills only (brown, green, solar and mixed tariffs).
Development set: `data/uk_electricity/dev/` (12 invoices, 5 layouts). Answer key: `tests/ground_truth_uk_electricity_dev.csv`.
Unseen set: `data/uk_electricity/unseen/` (35 invoices, locked). It is not opened until the code is frozen.

This document is a draft. The sections below are filled in as decisions are made.

## Findings from the dev set

### Where the L1 quantities came from (checked 13 Nov 2026)

In the baseline the local model read 12,450, 15,400 and 7,680 kWh for the three L1 invoices. The answer key says 460, 480 and 440.
On all three invoices the consumption is in a meter table:

```
METER TYPE PREV CURR USED (KWH) RATE (P) AMOUNT (£)
E19M-004921 Actual 12,450 12,910 460 26.50p £121.90
```

| Invoice | PREV | CURR | USED | Read by the model |
|---|---|---|---|---|
| D-01 | 12,450 | 12,910 | 460 | 12,450 (PREV) |
| D-02 | 15,400 | 15,880 | 480 | 15,400 (PREV) |
| D-03 | 7,680 | 8,120 | 440 | 7,680 (PREV) |

The model took the first number of the row, which is the previous meter reading. The price plausibility check caught all three (about 1p per kWh) and sent them to review.

The meter row checks itself:
- CURR - PREV = USED: 12,910 - 12,450 = 460
- USED x RATE = AMOUNT: 460 x 26.50p = £121.90 (D-02: 480 x 25.50p = £122.40, D-03: 440 x 25.80p = £113.52)

### Two totals that do not agree (D-02)

D-02 shows "TOTAL AMOUNT DUE £138.45" at the top and "TOTAL PAYABLE £142.19" at the bottom.
The lines add up to £142.19 (£135.42 + £6.77 VAT), so the top figure is wrong. The answer key uses £142.19.

## Rules from these findings

1. **Consumption comes from the USED column**, not from a meter reading. In a meter table the regex reader finds the header row (`PREV CURR USED`) and reads the columns by their position.
2. **A meter row is confirmed only when it checks itself:** CURR - PREV = USED and USED x RATE = AMOUNT (rounded to the penny).
3. **A quantity equal to a meter reading (PREV or CURR) always goes to review**, whichever reader produced it.
4. **When two totals on the same invoice disagree**, the invoice goes to review.

These rules are based on the three L1 invoices only. The other layouts (L2 to L5) still need to be checked.

## To be decided

- Consumption definition for day and night lines (L2, L3) and for solar import and export (L4).
- Location-based and market-based emissions: when a green tariff counts as 0 (REGO evidence or not).
- What the regex reader looks for in each layout.
- All reasons for sending an invoice to review.
- Risk: once the regex reader improves, both readers could agree on a wrong number (a meter reading, or one line of several). Rules 2 and 3 have to arrive together with the new regex reader, not after it.
- Measurement plan: known_layouts and new_layouts reported separately, each with its own prediction written before the run.
