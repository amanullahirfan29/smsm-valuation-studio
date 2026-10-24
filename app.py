"""SMSM valuation platform — launch with: streamlit run app.py"""
from __future__ import annotations
import json
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import streamlit as st

from valuation.engine import run_model, sensitivity
from valuation.importers import update_from_workbook, WorkbookImportError
from valuation.exports import report_json,report_html,report_csv

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'data'/'reference_inputs.json'
st.set_page_config(page_title='SMSM | Valuation Studio',page_icon='📈',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{max-width:1380px;padding-top:1.8rem}h1,h2,h3{color:#173351}div[data-testid="stMetric"]{border:1px solid #dce5f1;border-radius:12px;padding:14px;background:#f8fafc}
[data-testid="stSidebar"]{background:#122D4B}[data-testid="stSidebar"] *{color:#f3f7fe!important}
.summary{border-left:4px solid #427A9C;padding:10px 18px;background:#f3f7fb;border-radius:4px}
</style>''',unsafe_allow_html=True)

if 'input_data' not in st.session_state:
    st.session_state.input_data=json.loads(SOURCE.read_text(encoding='utf-8'))
    st.session_state.import_audit=[]
    st.session_state.last_updated=datetime.now(timezone.utc).isoformat()

def clear_editor_widget_state():
    prefixes=('ass_','co_','peer_','price_date_','period_end_','source_url_','memo_','account_review_','comparability_review_','approval_')
    for widget_key in list(st.session_state.keys()):
        if widget_key.startswith(prefixes):
            del st.session_state[widget_key]

data=st.session_state.input_data
nav=['Dashboard & Overview','Historical Financial Data','Forecast Assumptions','Valuation Results','Scenarios & Sensitivity','Sources, Validation & Export']
with st.sidebar:
    st.markdown('### SMSM | Valuation Studio')
    st.caption('MM6026 • AI-Assisted Business Valuation')
    page=st.radio('Navigation',nav,label_visibility='collapsed')
    st.divider()
    st.caption('VALUATION DATE')
    st.write('23 October 2026')
    st.caption('Reporting: IDR million; prices: IDR/share')
    if st.button('Reset to provisional reference',use_container_width=True):
        clear_editor_widget_state()
        st.session_state.input_data=json.loads(SOURCE.read_text(encoding='utf-8'))
        st.session_state.import_audit=[]
        st.session_state.last_updated=datetime.now(timezone.utc).isoformat()
        st.rerun()

# Process user edits first where appropriate, then recalculate using the identical pure engine.
if page=='Forecast Assumptions':
    st.title('Forecast assumptions')
    st.caption('Editable analyst assumptions (A/P); values are not independently observed facts. Updates trigger the same DCF engine used in regression tests.')
    case=st.selectbox('Scenario to edit',list(data['scenarios']),index=1)
    p=data['scenarios'][case]
    sections={
        'Growth and profitability':[('fy2026_growth','FY2026 revenue growth',100),('fy2027_growth','FY2027 growth',100),('growth_fade','Annual growth fade (percentage points)',100),('fy2026_ebit_margin','FY2026 EBIT margin',100),('terminal_ebit_margin','FY2031 EBIT margin',100),('tax_rate','Operating tax rate',100)],
        'Reinvestment and terminal':[('da_revenue','Depreciation / revenue',100),('capex_revenue','Capital investment / revenue',100),('fy2026_nwc_revenue','FY2026 NWC / revenue',100),('fy2031_nwc_revenue','FY2031 NWC / revenue',100),('terminal_growth','Terminal growth',100),('terminal_roic','Terminal sustainable ROIC',100)],
        'Risk and claims':[('wacc_shift','WACC shift (percentage points)',100),('nci_multiple','NCI book multiple',1),('operating_cash_reserve_revenue','Cash reserve / revenue',100),('cash_rollforward_extra','Additional June–October cash (Rp million)',1),('derivative_liability_fraction','Derivative recognized as claim',100)]}
    for section,fields in sections.items():
        with st.expander(section,expanded=section=='Growth and profitability'):
            cols=st.columns(2)
            for j,(key,label,scale) in enumerate(fields):
                with cols[j%2]:
                    val=float(p[key])*scale
                    fmt='%.2f' if scale==100 else '%.4f' if key=='nci_multiple' else '%.0f'
                    new=st.number_input(label,value=val,step=0.25 if scale==100 else 0.05 if key=='nci_multiple' else 10000.0,format=fmt,key=f'ass_{case}_{key}')
                    p[key]=new/scale
    st.divider()
    with st.expander('Cost of capital — observed and modeled market inputs',expanded=False):
        co=data['cost_of_capital']
        col1,col2=st.columns(2)
        for idx,(key,desc,scale) in enumerate([
            ('sovereign_yield','10-year sovereign yield (%)',100),('sovereign_spread','Default spread (%)',100),
            ('indonesia_total_erp','Total Indonesia equity risk premium (%)',100),('country_erp','Country risk premium (%)',100),
            ('domestic_exposure','Indonesia risk exposure (%)',100),('unlevered_beta','Unlevered industry beta (×)',1),
            ('bank_debt_cost','Bank debt cost (%)',100),('lease_debt_cost','Lease financing cost (%)',100),
            ('debt_tax_shield','Financing tax shield (%)',100),('nci_equity_weight_proxy','NCI capitalization proxy (Rp million)',1)]):
            with (col1 if idx%2==0 else col2):
                orig=float(co[key])*scale
                co[key]=st.number_input(desc,value=orig,step=.1 if scale==100 else .02 if key=='unlevered_beta' else 1000.0,format='%.3f' if scale==100 else '%.4f' if key=='unlevered_beta' else '%.0f',key=f'co_{key}')/scale
    st.caption('All controls are session-local; download a JSON audit to save calculated results. Upload a Stage4 workbook to restore documented assumptions.')

elif page=='Valuation Results':
    st.title('Valuation results & peer governance')
    with st.expander('Edit comparable-company inputs and review certification',expanded=False):
        st.warning('Peer multiples are NOT accepted automatically. A user must document source, accounting and economic comparability, and explicitly certify before the relative confidence gate can open.')
        for peer in data['peers']:
            st.markdown(f"**{peer['ticker']} — {peer['currency']}**")
            left,right=st.columns(2)
            with left:
                for key,label in [('price','Reference share price'),('shares_m','Shares outstanding (millions)'),('cash','Cash (peer currency, millions)'),('debt','Financial debt (millions)')]:
                    x=peer.get(key)
                    val=st.text_input(f'{peer["ticker"]}: {label}',value='' if x is None else str(x),key=f'peer_{peer["ticker"]}_{key}')
                    try:peer[key]=float(val) if val.strip() else None
                    except ValueError:peer[key]=None
            with right:
                for key,label in [('leases','Lease debt (millions)'),('other_ev_adjustment','Other EV adjustment (millions; signed)'),('ebit','Operating EBIT (millions)'),('da','D&A (millions)')]:
                    x=peer.get(key)
                    val=st.text_input(f'{peer["ticker"]}: {label}',value='' if x is None else str(x),key=f'peer_{peer["ticker"]}_{key}')
                    try:peer[key]=float(val) if val.strip() else None
                    except ValueError:peer[key]=None
            peer['market_price_date']=st.text_input(f"{peer['ticker']}: price date YYYY-MM-DD",value=peer.get('market_price_date',''),key=f"price_date_{peer['ticker']}")
            peer['financial_period_end']=st.text_input(f"{peer['ticker']}: financial period end YYYY-MM-DD",value=peer.get('financial_period_end',''),key=f"period_end_{peer['ticker']}")
            peer['source_url']=st.text_input(f"{peer['ticker']}: primary financial source URL",value=peer.get('source_url',''),key=f"source_url_{peer['ticker']}")
            peer['adjustment_memo']=st.text_area(f"{peer['ticker']}: accounting and business-economics memo (minimum 25 characters)",value=peer.get('adjustment_memo',''),height=85,key=f"memo_{peer['ticker']}")
            peer['accounting_reviewed']=st.checkbox(f"{peer['ticker']}: confirm EV and operating earnings accounting normalized",value=peer.get('accounting_reviewed',False),key=f"account_review_{peer['ticker']}")
            peer['comparability_reviewed']=st.checkbox(f"{peer['ticker']}: confirm business, growth, risk and cash conversion comparability",value=peer.get('comparability_reviewed',False),key=f"comparability_review_{peer['ticker']}")
            peer['user_validated']=st.checkbox(f"{peer['ticker']}: explicit analyst approval",value=peer.get('user_validated',False),key=f"approval_{peer['ticker']}")
            st.divider()
        if st.button('Apply peer updates and recalculate',type='primary'):
            st.session_state.last_updated=datetime.now(timezone.utc).isoformat()
            st.rerun()

elif page=='Historical Financial Data':
    st.title('Historical financial data')
    st.caption('Historical values loaded from the reconciled Stage 2B workbook. Known Stage 4 historical column/cache defects are bypassed.')
    upl=st.file_uploader('Upload updated Stage 2B or Stage 4 financial workbook (.xlsx)',type=['xlsx'],help='Imports documented hardcoded inputs only; ignores Excel formula caches.')
    if upl is not None and st.button('Validate and apply workbook',type='primary'):
        try:
            candidate,audit=update_from_workbook(upl.getvalue(),data)
            verification=run_model(candidate)
            if verification['status']=='BLOCKED':
                st.error('Upload rejected: '+ '; '.join(verification['errors']))
            else:
                clear_editor_widget_state()
                st.session_state.input_data=candidate
                st.session_state.import_audit.append({'file':upl.name,'kind':audit['kind'],'changes':audit['changed'],'uploaded_at':datetime.now(timezone.utc).isoformat()})
                st.session_state.last_updated=datetime.now(timezone.utc).isoformat()
                st.success(f"{audit['kind']} accepted. {len(audit['changed'])} changed hardcoded input(s). Downstream calculations will be recomputed from scratch.")
                st.rerun()
        except (WorkbookImportError,ValueError,KeyError,TypeError) as e:
            st.error(f'Input rejected: {e}')

# Session-level edits are never written to the cloud repository. Reload a saved model-input
# snapshot to continue an analysis after a browser session expires.
if page=='Historical Financial Data':
    with st.expander('Restore saved model inputs (JSON)',expanded=False):
        st.caption('Use a JSON input snapshot downloaded from Sources, Validation & Export. Unsupported files are rejected.')
        saved=st.file_uploader('Previously downloaded model inputs',type=['json'],key='saved_input_upload')
        if saved is not None and st.button('Validate and restore saved inputs'):
            try:
                from valuation.input_snapshots import import_input_snapshot
                restored=import_input_snapshot(saved.getvalue())
                checked=run_model(restored)
                if checked['status']=='BLOCKED':
                    st.error('Saved inputs rejected: '+'; '.join(checked['errors']))
                else:
                    clear_editor_widget_state()
                    st.session_state.input_data=restored
                    st.session_state.last_updated=datetime.now(timezone.utc).isoformat()
                    st.session_state.import_audit.append({'file':saved.name,'kind':'Saved input snapshot','changed':['Full session restore'],'uploaded_at':st.session_state.last_updated})
                    st.success('Model inputs restored and recalculated.')
                    st.rerun()
            except (ValueError,KeyError,TypeError,UnicodeDecodeError) as e:
                st.error(f'Saved input rejected: {e}')

result=run_model(data)
if result['status']=='BLOCKED':
    st.error('Material validation error — valuation and recommendation blocked: '+ '; '.join(result['errors']))
    with st.expander('Raw input and recovery',expanded=True):
        st.code('Use the Assumptions page to correct parameters, or Reset to provisional reference.')
    st.stop()

w=result['wacc'];cases=result['dcf'];base=cases['Base'];hist=result['historical']
fmt=lambda n:f'{n:,.1f}'
rupiah=lambda n:f'Rp {n:,.2f}'

if page=='Dashboard & Overview':
    st.title('PT Selamat Sempurna Tbk')
    st.caption('IDX: SMSM · 23 October 2026 valuation · Analyst DCF / peer-pricing reference platform')
    st.warning('**PROVISIONAL ESTIMATE** — mathematical calculations pass; peer selection and valuation-date claim proxies do not justify a final Buy/Hold/Sell call.')
    c=st.columns(4)
    for col,label,val in zip(c,['Market close','Market capitalization','Base DCF value','Base modeled upside'],[f"Rp {result['market']['price']:,.0f}",f"Rp {w['market_cap']/1000:,.1f} bn",rupiah(base['per_share']),f"{base['upside']:+.1%}"]):col.metric(label,val)
    left,right=st.columns([1.35,1])
    with left:
        st.subheader('DCF scenario comparison')
        st.bar_chart([{'Case':name,'Rp / share':price} for name,price in [('Bear',cases['Bear']['per_share']),('Market',result['market']['price']),('Base',base['per_share']),('Bull',cases['Bull']['per_share'])]],x='Case',y='Rp / share')
    with right:
        st.subheader('Method reliability')
        st.info('DCF: executable and benchmark-reconciled, subject to economic assumptions.')
        st.warning('Relative: indicative only. ATMU acquisition and AUTO incomplete capitalization; DCI conditional.')
        st.write(f"**Recommendation:** {result['decision']['final_recommendation']}")
        st.write(f"**Terminal share of EV:** {base['terminal_fraction']:.1%}")
        st.write(f"**WACC:** {w['wacc']:.3%}")
    st.markdown('<div class="summary">Primary method: FCFF discounted at nominal-IDR WACC. Financial data are from the Stage 2B source. The published 23 October 2026 share count, beta, October cash roll-forward and NCI economic values still require confirmation.</div>',unsafe_allow_html=True)

elif page=='Historical Financial Data':
    st.subheader('Audited and restated annual history')
    annual=[]
    for h in hist['annual']:
        annual.append({'Year':h['year'],'Source class':h['type'],'Revenue Rp m':h['revenue'],'EBIT Rp m':h['ebit'],'D&A Rp m':h['da'],'EBITDA Rp m':h['ebitda'],'Parent NI Rp m':h['parent_net_income'],'Operating CFO Rp m':h['operating_cash_flow'],'NWC Rp m':h.get('nwc'),'Δ NWC Rp m':h.get('delta_nwc')})
    st.dataframe(annual,use_container_width=True,hide_index=True)
    st.subheader('H1 comparative and TTM operating metrics')
    ttm=hist['ttm']
    st.dataframe([{'Metric':k,'TTM June 2026 Rp m':v,'Classification':'Derived / normalized' if 'normalized' in k else 'Derived (H1 2025 rounded)'} for k,v in ttm.items()],hide_index=True,use_container_width=True)
    st.caption('A full historical TTM FCFF is not calculated: H1 2025 D&A, comprehensive NWC and CapEx comparatives are incomplete.')
    with st.expander('Recent data-import audit'):
        st.json(st.session_state.import_audit or [{'note':'Initial embedded Stage 2B historical dataset'}])

elif page=='Forecast Assumptions':
    st.divider();st.subheader('Current scenario output')
    col=st.columns(4)
    for s,(label,fn) in enumerate([('Cost of equity',lambda: w['cost_of_equity']),('Base WACC',lambda:w['wacc']),('Base share value',lambda:base['per_share']),('Terminal EV %',lambda:base['terminal_fraction'])]):
        col[s].metric(label,(f'{fn():.3%}' if s in (0,1,3) else rupiah(fn())))
    st.subheader('Active forecast — '+case)
    st.dataframe([{**{'FY':x['year']},**{k:round(x[k],2) for k in ('revenue','ebit','operating_taxes','da','capex','nwc','delta_nwc','fcff')}} for x in cases[case]['forecast']],hide_index=True,use_container_width=True)

elif page=='Valuation Results':
    st.title('Market, DCF and relative calculations')
    st.caption('All monetary columns in Rp million unless per-share.')
    c1,c2,c3=st.columns(3)
    c1.metric('Cost of equity',f'{w["cost_of_equity"]:.3%}')
    c2.metric('WACC',f'{w["wacc"]:.3%}')
    c3.metric('Base enterprise value',f'Rp {base["enterprise_value"]/1000:,.1f} bn')
    st.subheader('Forecast FCFF and present value')
    st.dataframe([{k:round(v,3) for k,v in x.items()} for x in base['cashflows']],hide_index=True,use_container_width=True)
    left,right=st.columns(2)
    with left:
        st.subheader('DCF components')
        st.dataframe([{'Component':label,'Rp million':round(v,2)} for label,v in [('PV explicit FCFF',base['explicit_pv']),('PV terminal value',base['terminal_pv']),('Operating enterprise value',base['enterprise_value']),('Parent equity value',base['equity_value'])]],hide_index=True,use_container_width=True)
        st.metric('Value per common share',rupiah(base['per_share']))
    with right:
        st.subheader('Equity-bridge detail')
        br=base['bridge']
        st.dataframe([{'Component':k.replace('_',' ').capitalize(),'Rp million':round(br[k],2)} for k in ('oct_cash_proxy','operating_cash_reserve','excess_cash','term_deposits','associate_value_proxy','other_investment_proxy','bank_debt','lease_debt','nci_value_proxy','derivative_proxy','scenario_bridge')],hide_index=True,use_container_width=True)
    st.subheader('Comparable company calculations')
    shown=[]
    for p in result['peers']:
        shown.append({'Ticker':p['ticker'],'Currency':p['currency'],'EV/EBITDA':round(p['ev_ebitda'],2) if p['ev_ebitda'] else 'Missing','EV/EBIT':round(p['ev_ebit'],2) if p['ev_ebit'] else 'Missing','Indicative price via EBITDA':round(p['smsm_indication_ebitda'],2) if p['smsm_indication_ebitda'] else '—','Peer approved':'Yes' if p['multiple_approved'] else 'No','Notes':p['notes']})
    st.dataframe(shown,hide_index=True,use_container_width=True)
    if result['decision']['relative_publishable']:
        st.info(f"Reviewed peer EV/EBITDA indication: Rp {result['decision']['relative_range'][0]:,.2f}–Rp {result['decision']['relative_range'][1]:,.2f}/share; median Rp {result['decision']['relative_median']:,.2f}. Not automatically blended with DCF.")
    else:
        st.warning('Relative indications are provisional diagnostics, not used for final fair value or recommendation. At least two documented and expressly approved peers are required.')

elif page=='Scenarios & Sensitivity':
    st.title('Scenarios & sensitivity')
    st.dataframe([{'Scenario':k,'WACC':f'{v["wacc"]:.3%}','EV Rp bn':round(v['enterprise_value']/1000,2),'Equity Rp bn':round(v['equity_value']/1000,2),'Price Rp/share':round(v['per_share'],2),'Upside':f'{v["upside"]:+.1%}','Terminal dependence':f'{v["terminal_fraction"]:.1%}'} for k,v in cases.items()],hide_index=True,use_container_width=True)
    st.line_chart({k:[x['fcff']/1000 for x in cases[k]['forecast']] for k in cases})
    kind=st.selectbox('Sensitivity recalculated from the financial engine',['WACC × terminal g','Growth × EBIT margin','CapEx × NWC intensity','NCI × excess cash'])
    z=sensitivity(data,kind)
    grid=[]
    for f,row in zip(z['row_factors'],z['values']):
        grid.append({'Row shift':f'{f:+.2%}' if kind!='NCI × excess cash' else f'{f:+.2f} NCI ×',**{f'{c:+.2%}' if kind!='NCI × excess cash' else f'Rp {c*1000:+.0f} bn': None if x is None else round(x,2) for c,x in zip(z['col_factors'],row)}})
    st.dataframe(grid,hide_index=True,use_container_width=True)
    st.caption('WACC and terminal growth grids independently discount the forecast at each rate. Other grids re-run full operating forecasts and equity bridges.')

elif page=='Sources, Validation & Export':
    st.title('Sources, validation & export')
    st.write(f"**Data reviewed/updated UTC:** {st.session_state.last_updated}")
    from valuation.input_snapshots import export_input_snapshot
    st.download_button('Save editable model inputs (.json)',data=export_input_snapshot(data),file_name='smsm_valstudio_saved_inputs.json',mime='application/json',help='Save your current assumptions and imported historical data. Restore them via the Historical Financial Data page.')
    st.write('**Calculation status:** PROVISIONAL — numerically reproducible, external publication controlled.')
    with st.expander('Material documentation and validation warnings',expanded=True):
        for item in result['warnings']:st.warning(item)
    st.subheader('Accounting and model checks')
    checks=[('FY2025 reported revenue positive',hist['annual'][-1]['revenue']>0),('FY2025 D&A components reconcile',abs(hist['annual'][-1]['da']-184294)<1e-9),('Market capitalization = price × shares',abs(w['market_cap']-data['bridge']['price']*w['shares']/1e6)<.001),('WACC weights total 100%',abs(w['equity_weight']+w['debt_weight']-1)<1e-10),('FY2026 EBIT/tax/FCFF identity',abs(base['forecast'][0]['fcff']-(base['forecast'][0]['nopat']+base['forecast'][0]['da']-base['forecast'][0]['capex']-base['forecast'][0]['delta_nwc']))<.001),('Operating EV = sum of discounted components',abs(base['enterprise_value']-base['explicit_pv']-base['terminal_pv'])<.001),('Terminal growth below WACC',base['terminal_growth']<base['wacc']),('Recommendation withheld without 2 validated peers',result['decision']['final_recommendation']=='WITHHELD')]
    st.dataframe([{'Test':k,'Result':'PASS' if v else 'FAIL'} for k,v in checks],hide_index=True,use_container_width=True)
    st.subheader('Official sources and model limitations')
    for url in data.get('sources',[]):st.write(url)
    st.caption('The included workbooks contain line-level source notes and detailed accounting treatment. Uploaded workbooks are validated against an exact template; formula cached values are ignored.')
    st.subheader('Downloadable reports')
    col1,col2,col3=st.columns(3)
    col1.download_button('Download structured JSON',data=report_json(result,data),file_name='SMSM_valuation_results.json',mime='application/json',use_container_width=True)
    col2.download_button('Download summary CSV',data=report_csv(result,data),file_name='SMSM_valuation_scenarios.csv',mime='text/csv',use_container_width=True)
    col3.download_button('Download printable HTML',data=report_html(result,data),file_name='SMSM_valuation_report.html',mime='text/html',use_container_width=True)
    with st.expander('Input-upload history'):
        st.json(st.session_state.import_audit)
