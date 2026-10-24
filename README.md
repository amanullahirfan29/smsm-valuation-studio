[README.md](https://github.com/user-attachments/files/33909798/README.md)
# SMSM Valuation Studio — MM6026 Digital Business Valuation

**Company:** PT Selamat Sempurna Tbk (IDX: SMSM)  
**Valuation date:** 23 October 2026  
**Academic project:** MM6026 Mid-Term Exam — AI-Assisted Business Valuation Model  
**Implementation:** Python valuation engine + Streamlit web application

## 1. Live application and project repository

- **Public application:** https://smsm-valuation-studio-bcpsqf2emmgopwtmburdrr.streamlit.app
- **GitHub source:** https://github.com/amanullahirfan29/smsm-valuation-studio
- **Access:** The deployed application was successfully accessed in a Chrome Incognito session and on a real iPhone without a GitHub login during user acceptance testing on 24 October 2026. A standard web browser and internet access are needed to use the hosted version.
- **Valuation status:** **PROVISIONAL; formal investment recommendation WITHHELD.** Application availability and tested mathematical reconciliations do not certify all inputs or amount to investment advice.

The platform has six sections: **Dashboard & Overview**, **Historical Financial Data**, **Forecast Assumptions**, **Valuation Results**, **Scenarios & Sensitivity**, and **Sources, Validation & Export**.

## 2. What the model does

The financial workflow separates historical inputs, editable economic assumptions, Python valuation calculations, and scenario/report outputs:

1. **Market value:** compares an observed share price and share-count proxy with the model's estimated parent equity value.
2. **DCF:** forecasts nominal-IDR FCFF, discounts it at nominal-IDR WACC, includes the remaining FY2026 stub period and terminal value, and bridges operating enterprise value to parent common equity.
3. **Relative valuation:** calculates indicative EV/EBITDA and EV/EBIT diagnostics when inputs exist. A source-review/peer-approval gate prevents uncertified peer figures from being treated as a final relative fair value or an unconditional investment recommendation.
4. **User updateability:** allows controlled Excel imports, changes to forecast and capital-market assumptions, recalculated sensitivities, scenario switching, and report exports.
5. **Validation:** blocks material invalid inputs including terminal growth at or above WACC or sustainable ROIC; checks calculated identities, capitalization weights, and enterprise/equity reconciliation.

**Core formulas:** The model's capital structure convention includes a non-controlling-interest equity-weight proxy in `E`, and bank plus lease financing in `D`.


```text
Cost of equity = risk-free rate + beta × equity risk premium
WACC = E/(D+E) × Ke + D/(D+E) × Kd × (1 − financing tax shield)
FCFF = EBIT × (1 − operating tax rate) + D&A − CapEx − change in operating NWC
Operating enterprise value = PV(explicit FCFF) + PV(terminal value)
Parent equity value = operating EV + excess cash + nonoperating investments − financing claims − NCI and other economic claims
```

## 3. Default reference results (not independently certified market targets)

All valuations are conditional outputs from the reference model as of **23 October 2026**.

| Metric | Reference result |
|---|---:|
| Market close | Rp1,670/share |
| Approximate market capitalization | Rp9,617.0 billion |
| Cost of equity | 12.047% |
| Nominal IDR WACC | 11.968188% |
| Operating enterprise value | Rp11,977.489 billion |
| Parent equity value | Rp12,148.441 billion |
| Bear | Rp1,409.29/share |
| Base | Rp2,109.59/share |
| Bull | Rp2,988.01/share |
| Base modeled upside vs market | +26.3% |
| Formal investment recommendation | **WITHHELD** |

The model's Base DCF suggests possible undervaluation relative to the observed market price, but the Bear outcome and unresolved share-count/economic-claims/peer checks prevent an unconditional Buy/Hold/Sell call.

## 4. Run the application locally

**Prerequisites:** Python 3.10+, `pip`, and a modern web browser. Internet access is needed to install the listed dependencies if they are not cached locally.

**Windows PowerShell** (run from the cloned repository root):

```powershell
git clone https://github.com/amanullahirfan29/smsm-valuation-studio.git
cd smsm-valuation-studio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**macOS/Linux**:

```bash
git clone https://github.com/amanullahirfan29/smsm-valuation-studio.git
cd smsm-valuation-studio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the localhost URL shown by Streamlit, usually `http://localhost:8501`. Alternatively, Windows users can inspect `start_windows.bat` and macOS/Linux users can inspect `start_mac_linux.sh` in the repository. Local execution is separate from the public hosted instance.

**Run the independent valuation engine without Streamlit:**

```bash
python run_cli.py
```

**Run automated tests:**

```bash
python -m pytest -q
```

## 5. Using and updating the model

| Screen | Workflow |
|---|---|
| Historical Financial Data | Upload the provided `data/SMSM_Stage_2B_Reconciled_Financial_Data.xlsx` file, then press **Validate and apply workbook**. Supported import layouts are restricted to documented Stage 2B/Stage 4 formats. |
| Forecast Assumptions | Select Base, Bear, or Bull and edit revenue growth, EBIT margin, CapEx/D&A, operating working capital, terminal assumptions, or supported funding/claims inputs. Changes recalculate dependent results in Python. |
| Valuation Results | Review FCFF forecasts, WACC, EV, equity bridge, indicative peer diagnostics, and the peer-approval process. |
| Scenarios & Sensitivity | Compare Bear/Base/Bull values and sensitivity surfaces recomputed from the model; grids are not static image mockups. |
| Sources, Validation & Export | Review sources and validation status. Download structured JSON results, scenario CSV, printable HTML report, and editable model-input JSON. |

**Reproducible live-demo test:** With default saved inputs, Base FY2026 EBIT margin is **27.80%** and Base DCF value **Rp2,109.59/share**. Change that margin to **28.80%**; in the previously tested initial state the model changed to approximately **Rp2,113.09/share**. Restore **27.80%**, or restore the saved editable-input JSON, before concluding the demonstration. Actual results depend on the input state of the current session.

**Input persistence:** Edits are generally session-local and do **not** update the GitHub repository. Download the editable model-input JSON on the Sources/Validation/Export page and restore it on the Historical Financial Data page to resume a saved scenario.

**Data provenance:** The financial-input spreadsheet is in `data/`. The archived original Stage 4 workbook in `data/legacy/` is **not** a reliable historical-data baseline due to known H1 2026 mapping and formula-cache defects. Historical EBITDA/TTM values are recalculated from the reconciled Stage 2B sources; see `DATA_PROVENANCE.md`.

**Market updates:** The application supports structured manual updates and uploads; it does **not** promise live automatic market-data feeds. Real-time subscriptions or paid data integrations are not required for the currently deployed workflow. Avoid uploading personal/sensitive data to public repositories.

## 6. Validation evidence and technical scope

- **54 local automated Python tests** passed in the Stage 5B release test run; see `STAGE5B_TEST_REPORT.md`.
- The first GitHub Actions workflow run completed successfully after repository upload, including Python tests, CLI execution and Streamlit HTTP health checks. See the repository **Actions** tab for the authoritative workflow record.
- **24 October 2026 live user-acceptance testing:** public Incognito access; actual iPhone access and mobile tables/navigation; historical workbook import; forecast assumption propagation; Bear/Base/Bull and sensitivity values; JSON/CSV/HTML exports; editable-input save/restore; eight accounting/model checks; and invalid terminal-growth safeguards.
- A repeated HTTP 404 for a user-details endpoint was observed in the browser console while core functionality remained usable. This was judged **non-blocking in observed testing**, not conclusively diagnosed.
- The printable HTML report was checked via PDF print output. A user-selected 85% browser print scale fit its content on one sheet; print settings can differ between printers.

**Scope of tests:** Mathematical/technical checks and live UI tests support usability and internal consistency. They do **not** independently certify every valuation-date market observation, share-count claim, long-run forecast, NCI economic value or comparable-company input.

## 7. Financial limitations and decision rules

1. The 23 October 2026 issued-share count/treasury-share and dilution position requires contemporaneous confirmation; issued shares are currently a disclosed proxy.
2. June-to-October cash movements, operating-cash reserve, derivative and non-controlling-interest economic claims contain modeled assumptions rather than direct market observations.
3. ERP/beta, financing costs, tax normalization and terminal growth are judgmental market/economic inputs.
4. More than half the Base operating enterprise value is terminal value (approximately 60.8%), so results are sensitive to WACC, growth and sustainable reinvestment.
5. DCI multiples remain **indicative only**; ATMU/AUTO have missing or unapproved comparable-input components. At least two independently documented, source-reviewed comparables are required by **this application's approval rule** before publishing a relative value and considering a formal recommendation. The lecturer's brief does not independently specify a two-peer minimum.
6. The present result intentionally reports the **Bear–Bull conditional range, Base central DCF indication, market-price comparison and a WITHHELD formal recommendation**, rather than an unconditional BUY.

See `DATA_PROVENANCE.md`, the app's Sources/Validation/Export page and the corrected MM6026 presentation references for underlying evidence and qualifications.

## 8. Source structure and submission resources

```text
app.py                         Streamlit user interface
run_cli.py                     Independent, non-UI execution
requirements.txt               Python dependencies
data/reference_inputs.json      Default historical/forecast/bridge inputs
data/SMSM_Stage_2B_Reconciled_Financial_Data.xlsx
valuation/                      DCF/WACC/peer/sensitivity calculation engine and import/export modules
tests/                          Automated engine and UI smoke tests
.github/workflows/              CI configuration
DATA_PROVENANCE.md              Input-source mapping and historical corrections
STAGE5B_TEST_REPORT.md          54-test evidence and original release boundary
DEPLOYMENT_AUDIT.md             Deployment documentation
LIVE_UAT_CHECKLIST.md           Acceptance procedure (completed UAT summarized above)
```

**Useful source references:**

- SMSM 2025 annual report: https://smsm.co.id/uploads/attachment/Annual%20Report%20SMSM%202025.pdf
- SMSM company disclosure archive (including June 2026 interim report): https://smsm.co.id/id/otodoc.php
- Damodaran July 2026 country-risk discussion: https://aswathdamodaran.blogspot.com/2026/07/country-risk-drivers-measures-and.html
- Damodaran, *Investment Valuation* (2012), and MM6026 course slides provide valuation methodology.

**Repository status note — 24 October 2026:** The live site is deployed and user-acceptance testing has been completed. Earlier `TEST_REPORT.md` and `STAGE5B_TEST_REPORT.md` are historically dated release-stage evidence; their statements that browser tests had not yet run describe those earlier test environments, **not** the project's current UAT status. Do not retrospectively rewrite old test evidence; use this README and deployment/UAT evidence to document subsequent completion.
