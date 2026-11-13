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

## Location-based and market-based emissions

Both totals are reported for every invoice (dual reporting, as in the GHG Protocol Scope 2 Guidance).
The rule below was reviewed by the Sustainability Manager. The standards references (GHG Protocol quality criteria, ESRS E1-6) come from secondary sources and must be checked against the primary text before publication.

**Location-based** is computed on every invoice: confirmed kWh x grid factor from `data/emission_factors.csv`.

**Market-based = 0 only when all three hold:**
1. The invoice text says "REGO" and gives the scope ("100%" or a kWh amount).
2. The REGO statement is on this invoice itself (in the tariff or supply section), not only in a footer slogan or a separate document. A statement on the invoice is taken as covering this billing period and this supply. This is an assumption: a full audit also needs the supplier's REGO or fuel mix disclosure for the year.
3. The kWh are confirmed by the consumption rules (for a meter table: rule 2 above).

**Market-based = review** means: no market-based number is written, the reason is recorded, and a human checks the evidence. It does not stop the invoice: when the location-based fields are confirmed, the invoice is processed and its location-based total counts. Market-based goes to review when:
- the tariff has a label without REGO evidence ("green", "100% renewable", "eco", "solar", "mixed");
- a percentage is given without REGO evidence, or only a share of the supply is covered;
- the tariff name and the invoice text contradict each other.

**Market-based = location-based** for tariffs with no green claim (brown tariffs). The residual mix is not available, so the record says `market_basis = grid_average_fallback`. The two totals are equal because of this fallback, not by accident. The code does not use a residual mix until a factor with its source and year is added to `emission_factors.csv`.

**Not zero:** a "Solar Electricity" tariff label without exported energy on the invoice is a supplier label, not on-site generation.

**Checks that catch a wrong value:**
- `market_based = 0` requires `market_basis = REGO` and the word "REGO" in `evidence_text`, otherwise error.
- `market_based > location_based` goes to review.
- An invoice period that crosses a year boundary goes to review (no pro-rata policy yet).

**Fields kept for the audit trail:** `factor_value`, `factor_source`, `factor_year`, `method` (location or market), `market_basis` (REGO, residual_mix, supplier_specific, grid_average_fallback, unknown), `evidence_text`, `evidence_page`.

**Dev set (answer key):**

| Invoice | Tariff text | Market-based |
|---|---|---|
| D-03 | "100% REGO" in the tariff header, meter row checks itself | 0 |
| D-04 | "100% Renewable", no REGO | review |
| D-07, D-10 | "Green Electricity", no share, no REGO | review |
| D-09, D-12 | "Solar Electricity", no export | review |
| D-11 | "Mixed renewable", no share | review |
| D-01, D-02, D-05, D-06, D-08 | no green claim | same as location-based (`grid_average_fallback`) |

D-03 is the only dev invoice that reaches 0, so the zero path is tested on one invoice only.

Changes needed in `tests/ground_truth_uk_electricity_dev.csv` before the code is measured against it:
- D-04: `market_based_rule` from `zero` to `review` and `kg_co2e_market_based` empty (it is 0 now).
- D-07, D-09, D-10, D-11, D-12: `market_based_rule` from `unknown` to `review`, so the key uses the same words as this document.
- `expected_outcome` stays `process` for all of them: market-based review does not stop the invoice.

**Test factors:** the dev set uses the 2025 grid factor (0.177 kgCO2e/kWh) for all invoices, including periods in 2024-12 and 2026. This is intended for the test run only. Real runs select the factor year from the invoice period, and the 0.177 value is checked against the official DESNZ spreadsheet first.

## To be decided

- Consumption definition for day and night lines (L2, L3) and for solar import and export (L4).
- Pro-rata policy for invoice periods that cross a year boundary.
- Source and year of a UK residual mix factor.
- What the regex reader looks for in each layout.
- All reasons for sending an invoice to review.
- Risk: once the regex reader improves, both readers could agree on a wrong number (a meter reading, or one line of several). Rules 2 and 3 have to arrive together with the new regex reader, not after it.
- Measurement plan: known_layouts and new_layouts reported separately, each with its own prediction written before the run.
