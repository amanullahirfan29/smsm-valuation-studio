# Data provenance & discovered Stage 4 defects

## Source hierarchy

1. Company-reported/audited financial statements and notes; inherited from the Stage 2B workbook.
2. Stage 4 source-backed economic assumptions and dated market-price observations.
3. Analyst estimates (documented and editable) and book-value economic proxies (explicitly provisional).

Model monetary units: **Rp million**, except prices **Rp/share** and counts of common shares. U.S. peer data are in **USD millions**, with no unsupported conversion of dimensionless EV/earnings multiples.

## Material discovery during Stage 5: prior Stage 4 Excel historical cells are inconsistent

Inspection of the supplied Stage4 workbook established that the source-workbook H1 2026 hardcoded values were accidentally mapped to column `G` of `02 Historical & TTM` (labelled H1 2025), then overwritten by rounded H1 2025 values for revenue/EBIT/profit. The actual H1 2026 `H` input column is blank. Thus some cached Stage4 TTM cells represent FY2025 less H1 2025 without adding H1 2026.

A separate Stage4 EBITDA cache also disagrees with its own verified depreciation/amortization inputs: for FY2025 the cached EBITDA was 3,090,635 Rp million, whereas the source-based calculation is:

```
FY2025 EBIT                              1,502,192
Owned PPE depreciation                    152,464
Right-of-use depreciation                  29,798
Intangible amortization                     2,032
------------------------------------------------
Correct unadjusted EBITDA               1,686,486 (Rp million)
```

The Stage4 FY2025 `ΔNWC` cache also carries 308,908, which is the H1 2026 movement, rather than the proper FY2025 movement of **209,007** (2,039,544 − 1,830,537).

Corrected TTM June 2026 estimates using disclosed figures:

```
TTM revenue       5,338,789 + 2,649,138 - 2,555,800 = 5,432,127
TTM EBIT          1,502,192 +   734,043 -   698,000 = 1,538,235
TTM EBITDA        1,686,486 +   832,959 -   772,700 = 1,746,745
Normalized TTM EBIT                            = 1,513,799
Normalized TTM EBITDA                          = 1,722,309
```

The H1 2025 inputs are rounded and must remain labelled as such; this corrected TTM does not imply a validated TTM FCFF.

**Impact:** The Stage 4 *forward* DCF relies on FY2025 revenue, normalized operating assumptions, FY2025 closing NWC, forecast CapEx assumptions and financing/bridge values; it remains arithmetically reproducible. The former Stage4 historical EBITDA-based peer indications are **not** accepted as reliable relative fair values. The current application recalculates relative indications from corrected TTM operating metrics where peer inputs are complete, and continues to withhold peer approval.

## Baseline numerical reconciliation

| Measure | Stage4 reference | Independent pure-Python engine | Difference |
|---|---:|---:|---:|
| Base WACC | 11.968188282959415% | 11.968188282959415% | 0 |
| Base operating EV, Rp million | 11,977,488.833523097 | 11,977,488.833523097 | 0 |
| Base parent equity, Rp million | 12,148,441.129211502 | 12,148,441.129211502 | 0 |
| Base value, Rp/share | 2,109.5894803912583 | 2,109.5894803912583 | 0 |
| Bear value, Rp/share | 1,409.2878587341581 | 1,409.2878587341581 | 0 |
| Bull value, Rp/share | 2,988.0149319576703 | 2,988.0149319576703 | 0 |

These are **numerical comparisons**, not independent verification of the economic forecasts or final stock recommendation. The Python engine has no dependence on cached spreadsheet-derived results.

## Financial judgement & controls

- Stage 4 FY2026 annualized FCFF is prorated from 23 October to 31 December. This is a **forecast approximation**, not actual October cash generation.
- The Stage 4 June–October cash estimate uses annualized FY2026 Base FCFF as a proxy and deducts July/August distributions; operating cash reserve is estimated from revenue. Treated as uncertain.
- NCI and associate carrying amounts are valuation proxies rather than observed economic prices.
- Global Auto Parts unlevered beta is a sector proxy rather than a true weighted beta from the three named peers.
- July 2026 Damodaran country-risk numbers and the October 2026 sovereign-yield quote are source-backed as recorded in Stage4. Economic country risk allocation remains an assumption.
- ATMU lease liabilities are **missing from the current Stage4 workbook** even though prior narrative research discussed possible figures; the app preserves missing fields, showing no complete multiple until verified input is provided. It does not fill this with an invented value.
- DCI can show conditional indicative EV multiples. AUTO remains incomplete and excluded.
- The app's source-linked input format includes date and publication constraints. Source dates require human review for newly uploaded data not in the original fixed template.

No difference above is silently netted or balanced away. The formulas and assumptions remain visible and testable.
