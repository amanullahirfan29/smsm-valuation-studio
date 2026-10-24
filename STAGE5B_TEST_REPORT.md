# Stage 5B — Re-tested deployment readiness

**Date:** 24 October 2026. **Release:** Cloud-ready source package.

## Tests actually executed here

- Command: `python -m pytest -q` — **54 passed in 0.26 s**.
- Command: `python run_cli.py` — Bear **Rp1,409.29**, Base **Rp2,109.59**, Bull **Rp2,988.01**, nominal-IDR WACC **11.968188%**, investment recommendation **WITHHELD**.
- Command: `python -m compileall -q app.py valuation tests run_cli.py` — completed successfully.
- Original `reference_inputs.json`, Stage2B workbook and archived Stage4 workbook SHA-256 digests were compared with the prior Stage5 project: **identical contents**.
- Test suite verifies Stage2B/Stage4 uploads, corrected historical EBITDA/TTM mapping, calculated FCFF and capital costs, cash and NCI sensitivities, scenario regressions, peer exclusion, export consistency, saved-input JSON round trips and invalid-input blocking.
- Six Streamlit page branches continue to pass mocked UI execution in the inherited `test_ui_smoke.py`; this is **not** a browser test.

## Streamlit/server checks not completed in this environment

- `import streamlit` failed: Streamlit not installed.
- Attempted `python -m pip install 'streamlit>=1.36,<2' --retries 0 --timeout 5`; package index did not resolve Streamlit. Consequently no live Streamlit HTTP health endpoint, rendered browser page or public Community Cloud site can be certified here.
- The included GitHub Actions workflow is designed to install dependencies, run the tests, execute `run_cli.py` and check the live Streamlit HTTP health route **after the user uploads the project to GitHub**. That workflow itself has not yet run.
- Complete the real browser checklist `LIVE_UAT_CHECKLIST.md` after actual deployment. Only mark pass after observed success.

## Financial control boundary

- Stage4 **forward DCF** still reproduces exact prior regression results. The historical Stage4 workbook has known H1 2026 column/cached EBITDA/NWC defects; the archived original is not a valid historical dashboard baseline.
- Correct historical FY2025 D&A **184,294**, EBITDA **1,686,486**, NWC change **209,007** (Rp million); TTM Jun 2026 revenue **5,432,127**, normalized EBIT **1,513,799**, normalized EBITDA **1,722,309** (Rp million). H1 2025 comparator source values are rounded.
- Cost of capital, future forecast assumptions, treasury/dilution, NCI, nonoperating cash and peer adjustments remain provisional; recommendation must stay **WITHHELD** until financial review gates pass.

## Release assessment

**Package:** ready to upload to GitHub and deploy for real acceptance testing. **Live website:** not created. **Browser UAT:** outstanding. **Unconditional examination readiness:** not yet certified.
