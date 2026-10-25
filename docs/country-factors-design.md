# Country-aware emission factors: design (planned for v2)

Status: planned for v2, after v1.0. Not implemented in v1.0.
In v1.0 the UK DESNZ 2025 factors are applied to every invoice, whatever the country, and the README says so.

Decided on 25 Oct 2026. Postponed because the feature touches the schema, both readers, the hybrid merge, the policy, the invoice generator and the ground truth. v1.0 comes first.

## Goal
Read the country of an invoice and use the emission factor of that country.

## What depends on the country
| Activity | Country dependent | Approach |
|---|---|---|
| Electricity (Scope 2) | Yes, strongly | One grid factor per country (location-based, grid average). No factor for the country means no calculation: the invoice goes to review. There is no default country. |
| Natural gas and fuel (Scope 1) | Mostly no (combustion properties) | One default factor set with a documented source. Caveats: biofuel blends and gross versus net calorific value conventions differ by country. |

## Reading the country
- Signals: country name or code in the text (address), VAT number prefix, names in local languages.
- Regex reader: a dictionary of country names and aliases mapped to ISO 3166-1 alpha-2 codes. One country found gives the code; none or several give nothing.
- LLM reader: new field country (ISO code), null when the invoice does not say.
- Hybrid merge: same statuses as the other fields.
- Policy: for electricity the country is a critical field. Both readers must agree and the country must be found in the invoice text. For gas and fuel the country is recorded but not required.
- Unknown or unsupported country on an electricity invoice: review with the reason.

## Supported countries
To be confirmed: United Kingdom (existing), Portugal, Turkiye. Source, year and unit for each country go to docs/country-factors.md and are verified by a person before use.

## Out of scope
Market-based Scope 2, upstream emissions and grid losses (see docs/real-world-risks.md).

## Order of work
1. Sources and factor values (docs/country-factors.md)
2. Factor table and lookup by region, with tests
3. Schema, hybrid, policy, pipeline and report: the country field
4. Readers: regex country dictionary and the LLM field, with tests
5. Invoice generator and ground truth with countries, measured on a development set
6. A new unseen set that includes country cases, then one official run
