from __future__ import annotations
import json
from pathlib import Path
import pytest
from valuation.engine import run_model
from valuation.input_snapshots import export_input_snapshot,import_input_snapshot
from valuation.importers import update_from_workbook

ROOT=Path(__file__).resolve().parents[1]
SEED=json.loads((ROOT/'data'/'reference_inputs.json').read_text())

def test_saved_input_snapshot_roundtrip():
    raw=export_input_snapshot(SEED)
    restored=import_input_snapshot(raw)
    assert restored==SEED
    assert run_model(restored)['dcf']['Base']['per_share']==pytest.approx(run_model(SEED)['dcf']['Base']['per_share'])

def test_saved_inputs_change_updates_output():
    d=import_input_snapshot(export_input_snapshot(SEED))
    d['scenarios']['Base']['capex_revenue']+=.01
    assert run_model(d)['dcf']['Base']['per_share']<run_model(SEED)['dcf']['Base']['per_share']

def test_invalid_saved_inputs_rejected():
    for p in (b'',b'{broken',b'{}',b'a'*1_000_001):
        with pytest.raises((ValueError,UnicodeDecodeError,json.JSONDecodeError)):
            import_input_snapshot(p)

def test_suspicious_malformed_cutoff_rejected():
    x=json.loads(export_input_snapshot(SEED));x['payload']['valuation_date']='2026-10-24'
    with pytest.raises(ValueError):import_input_snapshot(json.dumps(x).encode())

def test_cloud_relative_source_paths():
    d=ROOT/'data'/'reference_inputs.json'
    assert d.is_file()
    legacy=ROOT/'data'/'legacy'/'ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx'
    assert legacy.is_file()
    assert (ROOT/'data'/'SMSM_Stage_2B_Reconciled_Financial_Data.xlsx').is_file()

def test_stage4_original_still_imports_after_archiving():
    b=(ROOT/'data'/'legacy'/'ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx').read_bytes()
    d,a=update_from_workbook(b,SEED)
    assert not a['changed'] and a['kind'].startswith('Stage4')

def test_peer_invalid_dates_cannot_approve():
    import copy
    d=copy.deepcopy(SEED)
    p=next(z for z in d['peers'] if z['ticker']=='DCI')
    p.update(user_validated=True,accounting_reviewed=True,comparability_reviewed=True,adjustment_memo='Full accounting and comparative note documented',market_price_date='2026-02-99',financial_period_end='2026-07-31',source_url='https://www.sec.gov/example')
    out=run_model(d)
    assert not next(z for z in out['peers'] if z['ticker']=='DCI')['multiple_approved']
