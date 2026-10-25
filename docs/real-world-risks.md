# Risks for real data (backlog, not implemented)

Problems to expect once the pipeline meets real invoices. Nothing here is built yet. "Today" describes what the pipeline does now.

Priority before real data: (1) region-specific factors, (2) per-file error handling, (3) currency-aware price bands, (4) audit trail, (5) aggregation of multi-line invoices, (6) OCR for scans.

## Documents and robustness
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Scanned or photographed PDFs | No text layer, the readers see nothing | Goes to review because nothing agrees | OCR step and an image quality flag |
| Corrupt PDF, password-protected file, Ollama not running | One failure should not stop a batch | Not handled: the exception most likely stops the whole folder run | Catch errors per file and send the file to review with the error |
| Several invoices in one PDF, or detail pages after a summary page | A PDF is read as one invoice | Not tested | Split by page or invoice number, page-aware reading |
| Invoices in other languages | Labels differ | The LLM can read them, the regex cannot; the type must be confirmed by both, so they go to review | Language detection and translated label lists |

## Quantities and units
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Several quantity lines (day and night tariff, several meters or sites, reactive energy kVArh, peak demand kW) | The right quantity is a sum or one specific line | Not handled: a wrong pick can pass the checks, because the number is in the text and the price per unit stays plausible | Read all candidate lines with their labels, sum tariff lines, ignore kVArh and kW |
| Estimated versus actual reads, corrections and rebills | Estimates are legitimate but should be flagged; corrections must offset earlier invoices | Negative quantities go to review; overlapping periods are not checked | Flag estimates, reconcile credit notes with the invoices they correct |
| Units outside the factor table (GJ, MJ, MWh for gas, kg for LPG) | No matching factor | Goes to review (schema or factor lookup rejects it) | Add conversions with their source, such as the calorific value |
| Gas billed in m3 with a kWh conversion on the invoice | The factor can be applied to m3 or to kWh and the results differ slightly | Depends on which number the readers pick | Prefer the energy figure (kWh) when the invoice shows it |

## Fuel
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Product names (gas oil, heating oil, HVO, biodiesel blends, LPG, AdBlue) | Different factors, and some products are not fuel for emissions | Unknown names go to review | A product dictionary maintained with domain input, one factor per product |
| Fuel-card statements with many fill-ups, mixed diesel and petrol | The quantity is a sum and the fuel type is per line | Not handled: one quantity and one fuel type per document | Line-item extraction with a fuel type per line |

## Dates and periods
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Month names, month-only periods, other date formats and languages, two-digit years | A missing period means no reporting period | Not parsed, period missing, goes to review | Extend the parser and test it on a fresh set first |
| Period spanning a year boundary | Emissions belong to two reporting years | Not split | Allocate by days between the years |
| Invoice date confused with the service period | Wrong period | Not tested | Check the period against the invoice date |
| Factor year differs from the activity year | Wrong factor year | Not checked | Warn when the years differ and use the factor of the matching year |

## Money
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Currencies and price levels (TRY, GBP, high inflation) | The price check bands are on a euro scale | Invoices in other currencies may fail the price check and go to review | Bands per currency, or skip the check when the currency is unknown |
| VAT included or excluded, totals that differ from the sum of the lines | The price per unit moves | Bands are wide, so small differences are tolerated | Prefer the net amount when present |

## GHG method
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Country or grid region | Factors differ by country; the table is UK DESNZ 2025 and the lookup ignores the region column | The same factors are applied to every invoice whatever the country, which is wrong for non-UK invoices | Detect the country (supplier, address, currency), match factors by region, review when missing (see docs/country-factors-design.md) |
| Scope 2 market-based versus location-based | The GHG Protocol asks for both; green tariffs and certificates change the market-based figure | Only one electricity factor | A second factor column and detection of renewable-tariff statements |
| Upstream emissions and losses (well-to-tank, transmission and distribution) | Scope 3 category 3 | Not included | Optional separate factors and a scope column |
| Gaps and overlaps in a supplier's monthly series | Missing months or double counting | Exact duplicates only | A series check per supplier and site |

## Data protection and audit
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Site, meter and customer identity | Emissions are reported per site or entity, and an invoice may belong to another entity | Supplier only | Extract the meter or site id and match it against a register |
| Audit trail | Assurance needs evidence for every number | Partly: both readers' values, the reasons and the factor source and year are kept | Keep the file hash, source snippet and page, reviewer decision and factor table version |
| Personal and commercial data in invoices and outputs | Privacy | Everything runs locally; the Excel output contains suppliers and amounts | Access control, anonymised test data, retention rules |

## Model operations
| Risk | Why it matters | Today | Possible rule |
|---|---|---|---|
| Model updates and drift | Behaviour changes silently | The model name is configurable, its version is not logged | Pin the model version, log it, rerun the fixed evaluation sets after changes |
| Text in an invoice that tries to instruct the model (prompt injection) | The model could be steered | Not tested; schema-constrained output and the checks against the text limit the damage | Test with adversarial invoices |
| Speed | About 4 seconds per invoice with the 3B model | Fine for hundreds of invoices | Cache by file hash, batch runs |
