# SMSM Valuation Studio — Live Acceptance Test (complete after deployment)

Record site URL: _____________________   Date/time: _________________   Tested by: ______________

Check each action in the REAL deployed browser. This file is **not** a completed test report.

- [ ] Open the `.streamlit.app` URL in a fresh/incognito browser. Dashboard loads with valuation date **23 October 2026** and PROVISIONAL label.
- [ ] Dashboard Base approximately **Rp2,109.59/share**, Bear **Rp1,409.29**, Bull **Rp2,988.01**, WACC **11.968188%**. Confirm no unexpected error.
- [ ] Navigate to all six pages; charts and tables display without truncated data or exceptions.
- [ ] Historical Financial Data: FY2025 **D&A 184,294 Rp million**, EBITDA **1,686,486 Rp million**, ΔNWC **209,007 Rp million**.
- [ ] TTM June 2026: revenue **5,432,127 Rp million**, normalized EBIT **1,513,799**, normalized EBITDA **1,722,309**. Roundness/estimates are disclosed.
- [ ] Forecast Assumptions: select Base, increase FY2026 EBIT margin by 1 percentage point; verify FCFF and price change. Reset reference.
- [ ] Upload included Stage 2B workbook; click Validate and apply; observe 0 unintended changes and valid valuation.
- [ ] Upload the archived original Stage 4 workbook; verify its prior historical caches are ignored and valid assumptions import.
- [ ] Scenarios & Sensitivity: switch sensitivity type; 5×5 grid recalculates and its center equals Base price.
- [ ] Valuation Results: AUTO incomplete, no final peer range / recommendation; explanatory warnings visible.
- [ ] Sources, Validation & Export: JSON, CSV and HTML download, open, and agree on Base value and WITHHELD status.
- [ ] Download **Save editable model inputs (.json)**, change one assumption, restore earlier snapshot via Historical Financial Data; figures return to prior state.
- [ ] Browser refresh starts a fresh session as expected; same site works on mobile or a second browser.
- [ ] Copy actual public URL and ask another person to load the site (without signing in) to verify sharing.

**Acceptance decision:** [ ] PASS [ ] FAIL — Notes: _____________________________________

Financial caveat: passing live UAT verifies application usability, not that market assumptions, peers or economic values are fully audited.
