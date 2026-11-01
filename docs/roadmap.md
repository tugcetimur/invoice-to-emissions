# Roadmap

## Done
- Phase 1: synthetic invoices and the emission factor table
- Phase 2: schema and calculation core
- Phase 3: regex reader, local LLM reader and hybrid merge
- Phase 4: validation rules, decision policy, end-to-end pipeline and Excel report
- Phase 5: fresh evaluation set (25 invoices), predictions committed before the run, one official run. Results: docs/fresh-set-results.md
- README and the v1.0 release
- v1.1: one-sheet workbook for a folder of invoices (scripts/make_footprint_excel.py), with nine synthetic UK sample invoices (data/uk_samples). Findings: docs/uk-samples-findings.md

## Next
- v2 (design document first): several products per invoice, consistency checks, market-based green electricity, more fuels, a better regex reader and a new unseen set to measure on

## Later
- Streamlit interface (issue #17)
- Country-aware emission factors (docs/country-factors-design.md) and the risks for real data (docs/real-world-risks.md)

## Current limitations
- Synthetic data only
- UK DESNZ 2025 emission factors are applied to every invoice, whatever the country
- Small local model (llama3.2:3b) and small test sets
- No scanned invoices (no OCR)
