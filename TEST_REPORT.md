# Stage 5 — Actual Test Results and Acceptance Record

**Date:** 24 October 2026 · **Application:** SMSM Valuation Studio · **Basis:** Stage2B/Stage4 uploaded workbooks.

## Environment and execution boundary

- Python valuation engine, workbook data importer, scenario/sensitivity logic and downloadable report generators were executed in the supplied runtime.
- `pytest` is installed and was used to execute the test suite.
- **Streamlit is not installed in this current environment** and attempted `pip install` failed because the runtime could not resolve the package repository. Accordingly **no live Streamlit server, HTTP port, or browser session has been verified** here. This is an explicit release-stage limitation, not a completed UI deployment test.
- Six application page branches were successfully executed with a **mock Streamlit interface** to catch pure-Python page construction mistakes; these mocked tests do not guarantee the real browser widget APIs or visual layout.

## Automated tests

```
$ python -m pytest -q
...............................................   [100%]
47 passed in 0.27s
```

The 47 passing tests include:

1. 11 strict Stage4 regression comparisons for actual WACC, market cap, cost of equity, explicit FCFF PV, terminal PV, EV, parent equity, Bear/Base/Bull per-share value and terminal-dependence fraction.
2. Normalized historical FY2025 EBIT/D&A/EBITDA and corrected TTM Jun2026 controls (Stage4 source cache defect fixed from Stage2B).
3. Assumption propagation: operating profit, CapEx, working capital, NCI, shares and market-price changes update expected dependent results.
4. Risk controls: invalid `g >= WACC`, `g >= stable ROIC`, missing shares, invalid shares, and invalid Excel uploads block appropriately.
5. Base-case cash-rollforward adjustment does not double-count its own assumption when edited.
6. Full-engine sensitivity center agrees with Base for WACC × growth, revenue growth × EBIT margin, CapEx × working-capital intensity and NCI × excess cash.
7. Independent algebraic agreement for discounted DCF PV, terminal reinvestment and FCFF identities.
8. Excel upload round trips for both supplied `.xlsx` source formats, including source workbooks with artificially changed hardcoded revenues, CapEx assumptions, 2025 working-capital inventory, and bank borrowings; dependent results recalculate.
9. Peer-data exclusion tests: AUTO lacks EV inputs, ATMU initially lacks lease data, peer approvals require documentation, and large peer/DCF disagreement prevents unconditional investment recommendation.
10. JSON/CSV/HTML exports agree with the same model used to populate the dashboard.
11. Source code compiles; **all six page branches pass mocked UI execution**.

## Actual numerical regression outcome

| Tested metric | Excel Stage4 reference | Python output | Difference |
|---|---:|---:|---:|
| WACC | 0.11968188282959415 | 0.11968188282959415 | 0 |
| Cost of equity | 0.12046790021739201 | 0.12046790021739201 | 0 |
| Explicit forecast PV, Rp m | 4,700,115.7073066 | 4,700,115.7073066 | 0 |
| Terminal value PV, Rp m | 7,277,373.126216496 | 7,277,373.126216496 | 0 |
| Operating enterprise value, Rp m | 11,977,488.833523097 | 11,977,488.833523097 | 0 |
| Parent common equity value, Rp m | 12,148,441.129211502 | 12,148,441.129211502 | 0 |
| Base per share, Rp | 2,109.5894803912583 | 2,109.5894803912583 | 0 |
| Bear per share, Rp | 1,409.2878587341581 | 1,409.2878587341581 | 0 |
| Bull per share, Rp | 2,988.0149319576703 | 2,988.0149319576703 | 0 |

The numbers above are model estimates and Excel regression targets; these tests do not independently establish economic truth or auditor-grade source verification.

## Model/output integrity caveat

**Do not describe the inherited Stage4 Excel file as entirely numerically correct.** Its historical H1 2026 mapping, historical FY2025 EBITDA cache and some historical NWC references were defective. The application reproduces the **forward DCF model outputs**, while recomputing historical/TTM and peer denominators from corrected actual source components. The input correction is detailed in `DATA_PROVENANCE.md`.

## Functional acceptance matrix

| Deliverable | Current status |
|---|---|
| Source code and standalone valuation engine | Implemented and executed |
| Stage2B and Stage4 Excel import with change propagation | Implemented and tested |
| Market value, WACC, FCFF, terminal value, EV and parent equity | Implemented and benchmark-reconciled |
| Bear/Base/Bull and four real-engine sensitivity families | Implemented and tested |
| Peer validation / exclusion and provisional relative indications | Implemented and tested |
| Recommendation governance / withheld status | Implemented and tested |
| Downloadable JSON, CSV, HTML reports | Implemented and tested |
| Six Streamlit page branches | Implemented, mocked UI execution passed |
| Actual installed Streamlit/browser interaction and visual responsiveness | **Not yet tested in this environment** |
| Public hosted deployment | Not implemented; not required for local use |
| Updated external financial source / final economic-claim verification | Partial; financial limitations disclosed |

## Minimum follow-up before lecturer presentation

On a machine with an internet connection and Python 3.10+, create a virtual environment, install `requirements.txt`, run `python -m streamlit run app.py`, and execute the 9-item live demonstration checklist in `README.md`. Confirm that: all six pages render, widget edits recalculate immediately, upload accepts both supplied workbooks, exports download and open correctly, and unsupported data remain blocked. This is a **user-side live acceptance test**, not something claimed complete in the current execution environment.

**Readiness:** *Core numerical engine ready and source package created.* Streamlit application is **ready for local installation and interactive acceptance testing**, but **not yet fully certified as browser-tested or final-investment-approved**.
