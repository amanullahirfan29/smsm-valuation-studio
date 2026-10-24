# Stage 5B deployment and validation record

- Existing Stage5 Python engine was preserved; only deployment packaging, user session recovery, source-file labeling and peer-date format checking were added.
- `data/reference_inputs.json`: seed values copied forward with no economic assumption changes.
- `data/SMSM_Stage_2B_Reconciled_Financial_Data.xlsx`: original Stage2B source preserved.
- `data/legacy/ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx`: unmodified Stage4 workbook retained for reference, **not** authoritative for H1 2026 and cached historical EBITDA / TTM measures.
- Historical financial metrics are recomputed from source components in Python (`valuation.engine.historical_view`).
- Saved-input JSON includes complete user session input values and supports later restore, not server-side permanent storage.
- GitHub Actions workflow included to execute unit tests on commits with Python 3.12 and required dependencies.
- The cloud **website has not been deployed from this environment**. A real Streamlit browser session must be tested using the checklist.
