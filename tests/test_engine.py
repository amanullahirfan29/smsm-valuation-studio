from __future__ import annotations
import ast
from copy import deepcopy
from datetime import date
from io import BytesIO
from pathlib import Path
import json,pytest,zipfile
from xml.etree import ElementTree as ET

from valuation.engine import run_model, calculate_wacc, project_financials, calculate_dcf, historical_view, sensitivity
from valuation.importers import XlsxInputReader, update_from_workbook, WorkbookImportError
from valuation.exports import report_json, report_csv, report_html

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data'/'reference_inputs.json').read_text())
BASE=run_model(D)

@pytest.mark.parametrize('key,actual',[
 ('wacc',lambda r:r['wacc']['wacc']),
 ('cost_of_equity',lambda r:r['wacc']['cost_of_equity']),
 ('market_cap',lambda r:r['wacc']['market_cap']),
 ('explicit_pv',lambda r:r['dcf']['Base']['explicit_pv']),
 ('terminal_pv',lambda r:r['dcf']['Base']['terminal_pv']),
 ('enterprise_value',lambda r:r['dcf']['Base']['enterprise_value']),
 ('parent_equity',lambda r:r['dcf']['Base']['equity_value']),
 ('price_per_share',lambda r:r['dcf']['Base']['per_share']),
 ('bear_share',lambda r:r['dcf']['Bear']['per_share']),
 ('bull_share',lambda r:r['dcf']['Bull']['per_share']),
 ('terminal_fraction',lambda r:r['dcf']['Base']['terminal_fraction']),
])
def test_stage4_forward_reference_matches(key,actual):
    assert BASE['status']=='PROVISIONAL'
    assert actual(BASE)==pytest.approx(D['reference'][key],rel=1e-12,abs=1e-7)

def test_confirm_corrected_historical_d_and_a():
    h=BASE['historical']['annual'][-1]
    assert h['ebitda']==1686486
    assert h['da']==184294
    assert h['delta_nwc']==209007

def test_corrected_ttm_mapping():
    t=BASE['historical']['ttm']
    assert t['revenue']==5432127
    assert t['normalized_ebit']==1513799
    assert t['normalized_ebitda']==1722309
    assert t['normalized_ebitda']!=2317935 # Stage4 cached incorrect output

def test_operating_earnings_increase_fcff():
    d=deepcopy(D);d['scenarios']['Base']['fy2026_ebit_margin']+=.01
    r=run_model(d)
    assert r['dcf']['Base']['forecast'][0]['fcff']>BASE['dcf']['Base']['forecast'][0]['fcff']

def test_more_capex_decreases_fcff():
    d=deepcopy(D);d['scenarios']['Base']['capex_revenue']+=.01
    assert run_model(d)['dcf']['Base']['forecast'][0]['fcff']<BASE['dcf']['Base']['forecast'][0]['fcff']

def test_more_nwc_investment_reduces_fcff():
    d=deepcopy(D);d['scenarios']['Base']['fy2026_nwc_revenue']+=.01
    assert run_model(d)['dcf']['Base']['forecast'][0]['fcff']<BASE['dcf']['Base']['forecast'][0]['fcff']

def test_increased_nci_reduces_parent_equity():
    d=deepcopy(D);d['scenarios']['Base']['nci_multiple']+=.2
    r=run_model(d)
    assert r['dcf']['Base']['equity_value']<BASE['dcf']['Base']['equity_value']

def test_share_count_changes_per_share_value():
    d=deepcopy(D);d['bridge']['treasury_adjustment']=100_000_000
    r=run_model(d)
    assert r['wacc']['shares']!=BASE['wacc']['shares']
    assert r['dcf']['Base']['per_share']!=pytest.approx(BASE['dcf']['Base']['per_share'])

def test_price_changes_market_value_and_wacc():
    d=deepcopy(D);d['bridge']['price']+=100
    r=run_model(d)
    assert r['market']['market_cap']>BASE['market']['market_cap']
    assert r['wacc']['wacc']!=pytest.approx(BASE['wacc']['wacc'])

def test_base_cash_extra_not_double_counted():
    d=deepcopy(D);d['scenarios']['Base']['cash_rollforward_extra']=100000
    new=run_model(d)
    b=new['dcf']['Base']['bridge']
    assert b['scenario_bridge']==pytest.approx(b['base_bridge'])

def test_invalid_terminal_growth_blocks():
    d=deepcopy(D);d['scenarios']['Base']['terminal_growth']=.20
    assert run_model(d)['status']=='BLOCKED'

def test_missing_critical_input_blocks():
    d=deepcopy(D);d['bridge']['issued_shares']=None
    r=run_model(d)
    assert r['status']=='BLOCKED' and r['errors']

def test_nonpositive_share_count_blocks():
    d=deepcopy(D);d['bridge']['treasury_adjustment']=d['bridge']['issued_shares']
    assert run_model(d)['status']=='BLOCKED'

def test_both_peer_gates_withhold_recommendation():
    assert BASE['decision']['final_recommendation']=='WITHHELD'
    assert not BASE['decision']['relative_publishable']
    assert all(not peer['multiple_approved'] for peer in BASE['peers'])

def test_auto_missing_ev_is_excluded():
    auto=next(p for p in BASE['peers'] if p['ticker']=='AUTO')
    assert auto['ev_ebitda'] is None and not auto['complete']

def test_dci_indicative_multiples():
    dci=next(p for p in BASE['peers'] if p['ticker']=='DCI')
    assert dci['ev_ebitda']==pytest.approx(15.745120143759738)
    assert dci['smsm_indication_ebitda']==pytest.approx(4738.748469104051)

def test_sensitivity_center_equals_base_dcf():
    for typ in ('WACC × terminal g','Growth × EBIT margin','CapEx × NWC intensity','NCI × excess cash'):
        z=sensitivity(D,typ)
        assert z['values'][2][2]==pytest.approx(BASE['dcf']['Base']['per_share'],abs=1e-6)

def test_dcf_term_value_and_fcff_math():
    b=BASE['dcf']['Base']
    assert b['enterprise_value']==pytest.approx(b['explicit_pv']+b['terminal_pv'])
    assert b['terminal_fcff']==pytest.approx(b['terminal_nopat']*(1-b['terminal_growth']/b['terminal_roic']))
    for f in b['forecast']:
        assert f['fcff']==pytest.approx(f['nopat']+f['da']-f['capex']-f['delta_nwc'])

def test_fcff_stub_uses_only_oct_dec():
    first=BASE['dcf']['Base']['cashflows'][0]
    assert first['future_fraction']==pytest.approx((date(2026,12,31)-date(2026,10,23)).days/365)
    assert first['future_fraction']<.20

def test_exports_match_dashboard():
    j=json.loads(report_json(BASE,D))
    assert j['scenarios']['Base']['per_share']==pytest.approx(BASE['dcf']['Base']['per_share'])
    assert j['recommendation']=='WITHHELD'
    c=report_csv(BASE,D).decode('utf-8-sig')
    assert '2109.5895' in c
    h=report_html(BASE,D).decode('utf-8')
    assert '2,109.59' in h and 'WITHHELD' in h

def test_stage2b_upload_roundtrip():
    p=ROOT/'data'/'SMSM_Stage_2B_Reconciled_Financial_Data.xlsx'
    d,a=update_from_workbook(p.read_bytes(),D)
    assert a['kind'].startswith('Stage2B') and not a['changed']
    assert run_model(d)['dcf']['Base']['per_share']==pytest.approx(BASE['dcf']['Base']['per_share'])

def test_stage4_upload_roundtrip():
    p=ROOT/'data'/'legacy'/'ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx'
    d,a=update_from_workbook(p.read_bytes(),D)
    assert a['kind'].startswith('Stage4') and not a['changed']
    assert run_model(d)['wacc']['wacc']==pytest.approx(BASE['wacc']['wacc'])

# Simulate one changed hardcoded XML input in a workbook, leaving its formula caches stale.
def change_cell_xlsx(xlsx:bytes,sheet_name:str,address:str,new_value:float)->bytes:
    wb=XlsxInputReader(xlsx)
    sheetpath=wb.paths[sheet_name]
    root=ET.fromstring(wb.z.read(sheetpath))
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    cell=next(c for c in root.findall('.//m:sheetData/m:row/m:c',ns) if c.attrib.get('r')==address)
    assert cell.find('m:f',ns) is None
    v=cell.find('m:v',ns)
    assert v is not None
    v.text=str(new_value)
    out=BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as dest:
        for info in wb.z.infolist():
            content=ET.tostring(root,encoding='utf-8',xml_declaration=True) if info.filename==sheetpath else wb.z.read(info.filename)
            dest.writestr(info,content)
    return out.getvalue()

def test_updated_source_2025_revenue_recalculates_model():
    original=(ROOT/'data'/'SMSM_Stage_2B_Reconciled_Financial_Data.xlsx').read_bytes()
    changed=change_cell_xlsx(original,'02 Historical Financials','F7',5500000)
    d,a=update_from_workbook(changed,D)
    assert '2025.revenue' in a['changed']
    r=run_model(d)
    assert r['status']=='PROVISIONAL'
    assert r['dcf']['Base']['forecast'][0]['revenue']>BASE['dcf']['Base']['forecast'][0]['revenue']
    assert r['dcf']['Base']['per_share']!=pytest.approx(BASE['dcf']['Base']['per_share'])

def test_updated_stage4_assumption_recalculates_model():
    original=(ROOT/'data'/'legacy'/'ORIGINAL_Stage4_KNOWN_HISTORICAL_CACHE_ERRORS.xlsx').read_bytes()
    changed=change_cell_xlsx(original,'03 Forecast Assumptions','C14',.06)
    d,a=update_from_workbook(changed,D)
    assert 'Base.capex_revenue' in a['changed']
    r=run_model(d)
    assert r['status']=='PROVISIONAL'
    assert r['dcf']['Base']['per_share']<BASE['dcf']['Base']['per_share']

def test_upload_rejects_non_xlsx():
    with pytest.raises(WorkbookImportError):update_from_workbook(b'not a workbook',D)

def test_upload_rejects_unrelated_workbook():
    with pytest.raises(WorkbookImportError):update_from_workbook(b'PK\x03\x04fake',D)

def test_ui_source_has_six_pages_and_compiles():
    src=(ROOT/'app.py').read_text()
    compile(src,'app.py','exec')
    for s in ['Dashboard & Overview','Historical Financial Data','Forecast Assumptions','Valuation Results','Scenarios & Sensitivity','Sources, Validation & Export']:
        assert s in src

def test_uploaded_working_capital_source_line_recalculates_fcff():
    file=(ROOT/'data'/'SMSM_Stage_2B_Reconciled_Financial_Data.xlsx').read_bytes()
    adjusted=change_cell_xlsx(file,'04 Working Capital','E11',1300326)  # +50,000m inventory, closing 2025 NWC higher
    cfg,audit=update_from_workbook(adjusted,D)
    r=run_model(cfg)
    assert cfg['historical'][-1]['nwc']==D['historical'][-1]['nwc']+50000
    assert r['dcf']['Base']['forecast'][0]['fcff']>BASE['dcf']['Base']['forecast'][0]['fcff']
    assert '2025.nwc' in audit['changed']

def test_uploaded_bank_borrowing_flows_to_wacc_and_bridge():
    original=(ROOT/'data'/'SMSM_Stage_2B_Reconciled_Financial_Data.xlsx').read_bytes()
    changed=change_cell_xlsx(original,'06 Capital Structure','E9',44835)
    cfg,a=update_from_workbook(changed,D)
    r=run_model(cfg)
    assert r['dcf']['Base']['bridge']['bank_debt']==BASE['dcf']['Base']['bridge']['bank_debt']+10000
    assert r['wacc']['debt_weight']>BASE['wacc']['debt_weight']

def test_relative_peer_documentation_gate_and_dispersion_control():
    d=deepcopy(D)
    for p in d['peers'][:2]:
        p['user_validated']=True
        p['accounting_reviewed']=True
        p['comparability_reviewed']=True
        p['adjustment_memo']='Reviewed acquisitions, GAAP leases and cash conversion differences.'
    d['peers'][0]['leases']=58.1
    d['peers'][0]['other_ev_adjustment']=-92.5
    r=run_model(d)
    assert r['status']=='PROVISIONAL'
    assert sum(p['multiple_approved'] for p in r['peers'])==2
    assert r['decision']['relative_publishable']
    assert r['decision']['final_recommendation']=='WITHHELD'  # ~2x DCF peer disagreement

def test_unverified_peer_cannot_be_certified_even_with_checkbox():
    d=deepcopy(D)
    p=d['peers'][0];p.update(user_validated=True,accounting_reviewed=True,comparability_reviewed=True,adjustment_memo='Covers correct accounting and business economics.')
    r=run_model(d)
    assert not r['peers'][0]['multiple_approved']  # ATMU lease balance still missing
