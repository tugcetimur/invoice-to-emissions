# Roadmap

## Done
- Phase 1: synthetic invoices and the emission factor table
- Phase 2: schema and calculation core
- Phase 3: regex reader, local LLM reader and hybrid merge
- Phase 4: validation rules, decision policy, end-to-end pipeline and Excel report

## Next (v1.0)
1. Phase 5: fresh evaluation set (25 invoices), pre-registered predictions, one official run. Design: docs/fresh-set-design.md (issue #16)
2. Phase 7: README, GitHub Actions and the v1.0 release (issue #18)

Next step: generate the 25 fresh invoices and their ground truth.

## After v1.0
- v1.1: Streamlit interface (issue #17)
- v2: country-aware emission factors and model improvements. See docs/country-factors-design.md and docs/real-world-risks.md

## Current limitations
- Synthetic data only
- UK DESNZ 2025 emission factors are applied to every invoice, whatever the country
- Small local model (llama3.2:3b) and small test sets
- No scanned invoices (no OCR)
