# SMSM Valuation Studio — MM6026 Digital Business Valuation

**PT Selamat Sempurna Tbk (IDX: SMSM)** · reference valuation date **23 October 2026**

A locally runnable six-page **Streamlit** application powered by a standalone, independently tested **Python valuation engine**. This is an application-based valuation platform, not a VBA workbook. It is the Stage 5 implementation for SBM ITB's MM6026 Mid-Term Examination.

> **Financial caution:** The valuation is **provisional**, not a fully certified investment recommendation. The default model deliberately withholds Buy/Hold/Sell because relative peers and some October-date economic claims are not yet fully documented. Blue-chip UI appearance does not establish investment accuracy.

## A. Quick start

Prerequisites: **Python 3.10+**, pip, a modern browser and internet access **at installation time** for Python packages (application operation needs no continuous internet connection).

**Windows PowerShell**

```powershell
cd SMSM_Valuation_Platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**macOS or Linux**

```bash
cd SMSM_Valuation_Platform
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

After launch, Streamlit normally displays a localhost address such as `http://localhost:8501`. Open the address **displayed by your own terminal**. There is **no deployed public URL**.

If Python reports `streamlit` is unavailable, run `python -m pip install -r requirements.txt` inside the virtual environment. The current build environment lacks Streamlit and cannot download it, so a browser-server smoke test remains to be performed on a machine with dependencies installed.

For a **no-Streamlit numerical execution**:

```bash
python run_cli.py
```

This runs all three scenarios and writes `SMSM_cli_valuation_results.json` in the extracted project directory.

## B. Navigation and operating instructions

| Page | Core functions |
|---|---|
| Dashboard & Overview | Provisional Market/DCF metrics, scenario comparison, method confidence and economic-risk notices |
| Historical Financial Data | Audited/restated historical data; TTM analysis; controlled `.xlsx` upload and audit of changed inputs |
| Forecast Assumptions | Edit Bear/Base/Bull revenue, margin, taxes, D&A, capital investment, working capital, cash/NCI assumptions and WACC market inputs |
| Valuation Results | Source-calculated FCFF/WACC/enterprise-to-equity reconciliation, peer inputs/multiples and controlled peer-approval checklist |
| Scenarios & Sensitivity | Three independently recomputed scenarios and sensitivities for risk, growth, reinvestment and non-operating claims |
| Sources, Validation & Export | Source URLs, status messages, input validation, JSON/CSV/printable-HTML report downloads |

**How to demonstrate calculation updateability:** Open *Forecast Assumptions → Base* and increase `FY2026 EBIT margin` by 1 percentage point. The following values update from the actual engine: 2026 EBIT, taxes, NOPAT, FCFF, discounted cash flows, enterprise value, common equity, and fair value per share. Return to the default values or use **Reset to verified sample**.

**How to import updated statements:** Open *Historical Financial Data*, upload either of the supplied exact-format workbooks, then click **Validate and apply workbook**. A file with mismatched/missing required worksheets or hardcoded inputs is rejected; valid input cells replace the original record and calculations are rerun in Python. Stage2B workbooks update reported historical inputs and NWC from underlying accounts. Stage4 workbooks update the **editable economic assumptions, WACC source inputs and bridge inputs**; Stage4 historical cached formulas are intentionally ignored because they contain a documented historical mapping defect.

**How to review peers:** The `Valuation Results` page contains a collapsible peer input/approval section. Update full capitalization and financial data, provide market and financial statement dates, source URL and an adjustment memorandum; explicitly confirm the financial and economic comparability reviews and certify peer approval. The relative valuation confidence gate requires **at least two sufficiently documented peers**; it will not approve AUTO while material inputs remain missing. Even with peer certifications, material DCF/relative disagreement keeps the investment recommendation withheld.

**Exports:** `Sources, Validation & Export` allows a snapshot JSON report, CSV of the three scenarios, and print-ready HTML. All three read from the same fresh model result displayed in the UI. They record the recommended status as **WITHHELD** when evidence is insufficient.

## C. Folder layout

```
SMSM_Valuation_Platform/
├── app.py                      # Streamlit interface / navigation
├── run_cli.py                  # independent command-line execution
├── requirements.txt
├── pytest.ini
├── README.md
├── DATA_PROVENANCE.md
├── TEST_REPORT.md
├── data/
│   ├── reference_inputs.json  # documented, edit-safe seed from Stage 2B + Stage 4
│   ├── SMSM_Stage_2B_Reconciled_Financial_Data.xlsx
│   └── ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx
├── valuation/
│   ├── __init__.py
│   ├── engine.py               # forecast, CAPM/WACC, DCF, bridge, peers, validation, sensitivities
│   ├── importers.py            # standard-library XLSX hardcode reader, template-specific imports
│   └── exports.py              # JSON, CSV, HTML reports
└── tests/
    └── test_engine.py         # 37+ automated tests
```

All runtime paths use the extracted directory as their base. Do not run `app.py` by double-clicking; use Streamlit through the terminal.

## D. Numerical reference tests

To run the tests:

```bash
python -m pytest -q
```

The forward DCF model, WACC and all three scenario prices are checked against values **read from the actual Stage4 Excel workbook**, with strict numerical tolerance. Core output values are **calculated**, never hardcoded in the engine or the interface.

Default reference regression targets:

- WACC: `0.11968188282959415`
- Base enterprise value: `11,977,488.833523097` **Rp million**
- Base parent equity: `12,148,441.129211502` **Rp million**
- Base fair value: `Rp 2,109.5894803912583/share`
- Bear fair value: `Rp 1,409.2878587341581/share`
- Bull fair value: `Rp 2,988.0149319576703/share`

These are Stage4 **numerical regression targets** and **analyst estimates**, not audited facts or guaranteed future market values.

## E. Financial and governance conventions

- **Market value:** 23 October 2026 closing price × issued shares net of user-specified treasury adjustment. Issued shares are a proxy pending a dated confirmation.
- **DCF:** Consolidated nominal-IDR operating FCFF discounted at nominal-IDR WACC; 2026 post-valuation stub, mid-period 2027–2031 explicit forecast, December 2031 terminal date.
- **WACC:** Local sovereign yield adjusted by default spread; mature ERP plus exposure-adjusted country ERP; bottom-up industry beta and capitalization-weighted debt/equity costs.
- **Terminal value:** Stable FY2032 NOPAT after reinvestment `g / stable ROIC`; invalid `g >= WACC` (or `g >= ROIC`) blocks the DCF.
- **Enterprise bridge:** Capitalized leases; NCI as separately valued minority claim; TRSS associate and eligible investments outside controlled EV; cash above operating liquidity reserve; derivative claims as explicit adjustable parameter.
- **Relative:** ATMU/DCI initially indicative only, AUTO excluded for missing EV/operating components. Foreign-company multiples are dimensionless; they are not converted using USD-IDR rates. Peer pre-cutoff prices are required.
- **Method:** DCF primary; peer multiple only if evidence gates pass. Formal recommendation **WITHHELD** unless required peer/documentation gates and material divergence tests pass.

The first version supports **manual Excel uploads**, not a real-time market-data connection. Automated data refresh is optional under the lecturer's instructions and is not claimed here.

## F. Limitations and security

1. **Historical Stage4 workbook defect:** H1 2026 was mislocated, and cached EBITDA / TTM values did not reconcile to disclosed D&A. The application reimports Stage2B financials and recalculates all historical EBITDA and TTM values correctly; see `DATA_PROVENANCE.md`.
2. **June–October 2026** balance-sheet roll-forward is a modeled estimate (not audited intermediate accounts).
3. **Risk-free benchmark, beta, capital costs, normalized taxes, NCI, associated investments, derivative claims and excess cash** are partly analyst estimates / economic proxies.
4. **Treasury shares and dilution** need a dated confirmation before unconditional per-share publication.
5. **Comparable peers** require further business and accounting normalization; the app does not falsely certify their original Stage4 indications.
6. **Uploaded Excel** is restricted to the Stage2B/Stage4 sheet structure; unsupported structures and missing critical inputs are rejected, and formula-cache values are never trusted.
7. **Streamlit live UI not executed in this environment** because package installation could not reach PyPI. All Python engine and import/export tests were executed; see `TEST_REPORT.md`. Run an actual local Streamlit session before the formal lecturer presentation.

## G. Suggested live demonstration checklist

1. Launch the Streamlit app; show overview and provisional label.
2. Show historical TTM revenue and normalized EBIT, and explain why these differ from the Stage4 Excel cache.
3. Edit Base EBIT margin, confirm FCFF and per-share values change; reset.
4. Edit a scenario and review the 5×5 WACC/terminal-growth sensitivity.
5. Upload the supplied Stage2B `.xlsx`, confirm zero unintended changes.
6. Show exclusion of incomplete AUTO/ATMU peers and the controlled review workflow.
7. Show model BLOCKED on `terminal g >= WACC`; reset.
8. Download CSV, HTML, JSON and explain they match the currently displayed model.
9. Run the automated suite: `python -m pytest -q`.

**The application is locally executable once Streamlit is installed; no live deployment or hosted URL is included.**


## Stage 5B — Cloud deployment additions

This release is arranged for GitHub's repository root. **Read `DEPLOYMENT_GUIDE.md`** for browser-only hosting steps and `LIVE_UAT_CHECKLIST.md` for required real-browser acceptance. The original Stage4 Excel workbook is archived in `data/legacy/` and explicitly labeled as containing known historical cache errors. The app uses its documented economic input defaults, not its defective historical caches.

Session editing is private to each current Streamlit session and **does not persist to your GitHub repo**. Download **Save editable model inputs (.json)** from the Sources page and restore that JSON on the Historical Data page whenever you need to recover edited settings. Do not upload personal or private files to a public repository.

As of this release, no hosted Streamlit site or completed real-browser UAT is claimed. Automatic unit tests in CI are an additional control, not a replacement for the live checklist.
