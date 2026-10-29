# Roadmap

## Done
- Phase 1: synthetic invoices and the emission factor table
- Phase 2: schema and calculation core
- Phase 3: regex reader, local LLM reader and hybrid merge
- Phase 4: validation rules, decision policy, end-to-end pipeline and Excel report
- Phase 5: fresh evaluation set (25 invoices), predictions committed before the run, one official run. Results: docs/fresh-set-results.md
- README

## Next
- v1.0 release: README with results and limitations, repository description, release notes (issue #18)

## After v1.0
- v1.1: Streamlit interface (issue #17)
- v2: country-aware emission factors (docs/country-factors-design.md), the gaps found on the fresh set (docs/fresh-set-results.md) and the risks for real data (docs/real-world-risks.md)

## Current limitations
- Synthetic data only
- UK DESNZ 2025 emission factors are applied to every invoice, whatever the country
- Small local model (llama3.2:3b) and small test sets
- No scanned invoices (no OCR)
