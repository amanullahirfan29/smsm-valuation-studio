"""Source-linked SMSM valuation engine. All currency figures IDR millions unless documented.

Replicates Stage 4 *forward* calculation logic, not its demonstrated defective
H1-2026 historical mapping / EBITDA TTM formula caches. No constants for output prices.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from typing import Any

VAL_DATE = date(2026, 10, 23)

class ModelError(ValueError):
    pass

def _num(value: Any, name: str, low: float | None = None, high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelError(f"Missing or non-numeric required input: {name}")
    value=float(value)
    if not (-1e100 < value < 1e100):
        raise ModelError(f"Invalid finite value: {name}")
    if low is not None and value < low: raise ModelError(f"{name} must be ≥ {low}")
    if high is not None and value > high: raise ModelError(f"{name} must be ≤ {high}")
    return value

def validate_inputs(data: dict) -> tuple[list[str],list[str]]:
    errors=[]; warnings=[]
    try:
        if data.get('valuation_date') != VAL_DATE.isoformat():
            errors.append('Valuation date must be 2026-10-23 for this reference case; select a documented data revision before changing date.')
        h=next((x for x in data['historical'] if x['year']==2025),None)
        if h is None: errors.append('FY2025 financial history missing')
        else:
            _num(h.get('revenue'),'FY2025 revenue',1)
            _num(h.get('nwc'),'FY2025 NWC')
        br=data['bridge']; co=data['cost_of_capital']
        _num(br.get('price'),'Closing market price',0.000001)
        _num(br.get('issued_shares'),'Issued common shares',1)
        treasury=_num(br.get('treasury_adjustment'),'Treasury/dilution adjustments',0)
        if br['issued_shares']-treasury <=0:errors.append('Economically outstanding shares must be positive')
        for field in ('bank_debt','lease_debt','nci_book','cash','term_deposits','associate_book','other_investments_book','derivative_liability'):_num(br.get(field),field,0)
        for field in ('sovereign_yield','sovereign_spread','indonesia_total_erp','country_erp','domestic_exposure','unlevered_beta','bank_debt_cost','lease_debt_cost','debt_tax_shield'):
            _num(co.get(field),field)
        if co['sovereign_yield'] <= co['sovereign_spread']: errors.append('Sovereign default spread must be below bond yield')
        if not 0<=co['domestic_exposure']<=1:errors.append('Domestic country-risk exposure outside 0–100%')
        if not 0<=co['debt_tax_shield']<1:errors.append('Financing tax-shield rate must lie [0,1)')
        for sc, p in data['scenarios'].items():
            for f in ('fy2026_growth','fy2027_growth','growth_fade','fy2026_ebit_margin','terminal_ebit_margin','tax_rate','da_revenue','capex_revenue','fy2026_nwc_revenue','fy2031_nwc_revenue','terminal_growth','terminal_roic','wacc_shift','nci_multiple','operating_cash_reserve_revenue','cash_rollforward_extra','derivative_liability_fraction'):
                _num(p.get(f),f'{sc}.{f}')
            if p['terminal_roic']<=0 or p['terminal_growth']<0 or p['terminal_growth']>=p['terminal_roic']:
                errors.append(f'{sc}: require 0 ≤ terminal growth < sustainable ROIC')
            if not 0<=p['tax_rate']<1: errors.append(f'{sc}: invalid operating tax rate')
            if not 0<=p['derivative_liability_fraction']<=1: errors.append(f'{sc}: invalid derivative fraction')
            if not 0<=p['operating_cash_reserve_revenue']<=1: errors.append(f'{sc}: invalid cash reserve ratio')
            if not 0<=p['nci_multiple']<=5: errors.append(f'{sc}: NCI proxy multiplier outside 0–5')
            if p['fy2026_ebit_margin']<=0 or p['terminal_ebit_margin']<=0: errors.append(f'{sc}: operating margin must be positive')
    except (KeyError,TypeError,ModelError) as e:
        errors.append(str(e))
    if data.get('cost_of_capital',{}).get('bank_debt')!=data.get('bridge',{}).get('bank_debt') or data.get('cost_of_capital',{}).get('lease_debt')!=data.get('bridge',{}).get('lease_debt'):
        warnings.append('WACC uses bridge debt/lease hardcodes as the single source of truth; legacy Stage4 WACC financing copy differs and is ignored.')
    warnings.extend([
        'Stage 4 H1 2026 mapping and historical EBITDA/TTM formula cache are defective; corrected from Stage 2B source lines.',
        '2025H1 EBIT/EBITDA comparisons are rounded; complete historical TTM FCFF is unavailable.',
        'The June–October cash roll-forward, equity claim proxies and operating cash floor are estimates.',
        'No official contemporaneous SMSM treasury-share confirmation; issued share count is a disclosed proxy.',
        'Market-derived cost of capital, 2026 financing rates and NCI economic values require economic judgment.',
        'ATMU/DCI multiples remain indicative; AUTO excluded until material EV inputs established.'
    ])
    return errors,warnings

def calculate_wacc(data:dict) -> dict:
    co=data['cost_of_capital']; br=data['bridge']
    shares=br['issued_shares']-br['treasury_adjustment']; market_cap=br['price']*shares/1_000_000
    if shares<=0 or market_cap<=0:raise ModelError('Invalid market shares or capitalization')
    d=br['bank_debt']+br['lease_debt']  # one source of truth: equity bridge financing inputs
    e=market_cap+co['nci_equity_weight_proxy']
    if e<=0:raise ModelError('Equity value must be positive')
    rf=co['sovereign_yield']-co['sovereign_spread']
    erp=co['indonesia_total_erp']-co['country_erp']+co['country_erp']*co['domestic_exposure']
    beta=co['unlevered_beta']*(1+(1-co['debt_tax_shield'])*d/e)
    ke=rf+beta*erp
    kd=(br['bank_debt']*co['bank_debt_cost']+br['lease_debt']*co['lease_debt_cost'])/d if d else 0
    w_e=e/(e+d);w_d=d/(e+d)
    wacc=w_e*ke+w_d*kd*(1-co['debt_tax_shield'])
    if wacc<=0:raise ModelError('WACC must be positive')
    return dict(market_cap=market_cap,shares=shares,rf=rf,erp=erp,beta=beta,cost_of_equity=ke,cost_of_debt=kd,equity_weight=w_e,debt_weight=w_d,wacc=wacc,total_capital=e+d)

def historical_view(data:dict) -> dict:
    rows=[]
    for h in sorted(data['historical'],key=lambda x:x['year']):
        x=deepcopy(h)
        required=['ppe_depreciation','rou_depreciation','amortization']
        x['da']=sum(float(x.get(k) or 0) for k in required) if all(x.get(k) is not None for k in required) else None
        x['ebitda']=x['ebit']+x['da'] if x['da'] is not None and x.get('ebit') is not None else None
        if h['year']==2025:
            x['delta_nwc']=h['nwc']-next(a['nwc'] for a in data['historical'] if a['year']==2024)
        rows.append(x)
    fy=next(h for h in rows if h['year']==2025)
    h1_25=data['interim']['2025H1'];h1_26=data['interim']['2026H1']
    ttm={}
    for k in ('revenue','ebit','parent_net_income'):
        if fy.get(k) is not None and h1_25.get(k) is not None and h1_26.get(k) is not None:
            ttm[k]=fy[k]+h1_26[k]-h1_25[k]
        else:ttm[k]=None
    ttm['ebitda']=fy['ebitda']+h1_26['ebit']+h1_26['da']-h1_25['ebitda'] if fy['ebitda'] is not None and h1_26['da'] is not None and h1_25['ebitda'] is not None else None
    ttm['normalized_ebit']=ttm['ebit']-h1_26['disposal_gain'] if ttm['ebit'] is not None else None
    ttm['normalized_ebitda']=ttm['ebitda']-h1_26['disposal_gain'] if ttm['ebitda'] is not None else None
    return dict(annual=rows,ttm=ttm,interim=deepcopy(data['interim']))

def project_financials(data:dict, scenario:str) -> list[dict]:
    p=data['scenarios'][scenario]
    fy=next(x for x in data['historical'] if x['year']==2025)
    last_rev=_num(fy.get('revenue'),'FY2025 revenue',1)
    last_nwc=_num(fy.get('nwc'),'FY2025 NWC')
    proj=[]
    for j,year in enumerate(range(2026,2032)):
        growth=p['fy2026_growth'] if j==0 else max(p['terminal_growth'], p['fy2027_growth']-(j-1)*p['growth_fade'])
        rev=last_rev*(1+growth)
        if rev<=0:raise ModelError('Forecast revenue nonpositive')
        margin=p['fy2026_ebit_margin'] if j==0 else p['fy2026_ebit_margin']+(p['terminal_ebit_margin']-p['fy2026_ebit_margin'])*j/5
        ebit=rev*margin
        tax=ebit*p['tax_rate'];nopat=ebit-tax
        da=rev*p['da_revenue'];capex=rev*p['capex_revenue']
        nwc_ratio=p['fy2026_nwc_revenue'] if j==0 else p['fy2026_nwc_revenue']+(p['fy2031_nwc_revenue']-p['fy2026_nwc_revenue'])*j/5
        nwc=rev*nwc_ratio; dnwc=nwc-last_nwc
        fcff=nopat+da-capex-dnwc
        proj.append(dict(year=year,revenue=rev,growth=growth,ebit_margin=margin,ebit=ebit,operating_taxes=tax,nopat=nopat,da=da,capex=capex,nwc_ratio=nwc_ratio,nwc=nwc,delta_nwc=dnwc,fcff=fcff,reinvestment=capex-da+dnwc))
        last_rev,last_nwc=rev,nwc
    return proj

def equity_bridge(data:dict, forecast:list[dict],wacc:dict,scenario:str)->dict:
    """Stage4 baseline: annualized June–October FCFF as unlevered cash proxy, not actual cash flow."""
    br=data['bridge'];p=data['scenarios'][scenario];base=data['scenarios']['Base'];shares=wacc['shares']
    days=(VAL_DATE-date(2026,6,30)).days
    div=(br['dividend_july_per_share']+br['dividend_aug_per_share'])*shares/1_000_000
    cash_generation=project_financials(data,'Base')[0]['fcff']*days/br['days_in_year']
    projected_cash=br['cash']+cash_generation-div+base['cash_rollforward_extra']
    cash_reserve=project_financials(data,'Base')[0]['revenue']*base['operating_cash_reserve_revenue']
    excess_cash=max(0,projected_cash-cash_reserve)
    nci=br['nci_book']*base['nci_multiple']
    deriv=br['derivative_liability']*base['derivative_liability_fraction']
    debt=br['bank_debt']+br['lease_debt']
    adjustment=excess_cash+br['term_deposits']+br['associate_book']+br['other_investments_book']-debt-nci-deriv
    # Stage4 scenario bridge: base bridge + NCI book multiplier delta,
    # operating-cash reserve percent delta times BASE revenue, + explicit extra cash shift.
    scen_adjust=adjustment+br['nci_book']*(base['nci_multiple']-p['nci_multiple'])+(base['operating_cash_reserve_revenue']-p['operating_cash_reserve_revenue'])*project_financials(data,'Base')[0]['revenue']+(p['cash_rollforward_extra']-base['cash_rollforward_extra'])
    return dict(jun_cash=br['cash'],cash_generation_proxy=cash_generation,days_elapsed=days,dividends_paid=div,oct_cash_proxy=projected_cash,operating_cash_reserve=cash_reserve,excess_cash=excess_cash,term_deposits=br['term_deposits'],associate_value_proxy=br['associate_book'],other_investment_proxy=br['other_investments_book'],bank_debt=br['bank_debt'],lease_debt=br['lease_debt'],nci_value_proxy=nci,derivative_proxy=deriv,base_bridge=adjustment,scenario_bridge=scen_adjust,notes='Annual FCFF proxy used June–October; book NCI and associate are not observed economic values.')

def calculate_dcf(data:dict,scenario:str,wacc:dict|None=None,forecast:list[dict]|None=None, wacc_override:float|None=None,terminal_growth_override:float|None=None)->dict:
    wacc=wacc or calculate_wacc(data)
    forecast=forecast if forecast is not None else project_financials(data,scenario)
    p=data['scenarios'][scenario]
    rate=wacc['wacc']+p['wacc_shift'] if wacc_override is None else wacc_override
    g=p['terminal_growth'] if terminal_growth_override is None else terminal_growth_override
    roic=p['terminal_roic']
    if not (0<=g<rate):raise ModelError(f'{scenario} terminal growth must satisfy 0 ≤ g < WACC')
    if g>=roic:raise ModelError('Terminal growth requires sustainable ROIC higher than growth')
    first_fraction=(date(2026,12,31)-VAL_DATE).days/365
    timing_first=first_fraction/2
    full_first=(date(2027,7,1)-VAL_DATE).days/365
    pv_exp=0.0; cashflows=[]
    for j,row in enumerate(forecast):
        frac=first_fraction if j==0 else 1.0
        t=timing_first if j==0 else (j-1)+full_first
        cf=row['fcff']*frac
        df=1/(1+rate)**t
        pv=cf*df
        cashflows.append(dict(year=row['year'],full_fy_fcff=row['fcff'],future_fraction=frac,post_date_fcff=cf,t=t,discount_factor=df,pv=pv))
        pv_exp+=pv
    last_ebit=forecast[-1]['ebit']
    terminal_ebit=last_ebit*(1+g)
    terminal_nopat=terminal_ebit*(1-p['tax_rate'])
    re_rate=g/roic
    terminal_fcff=terminal_nopat*(1-re_rate)
    terminal_value=terminal_fcff/(rate-g)
    terminal_horizon=(date(2031,12,31)-VAL_DATE).days/365
    pv_terminal=terminal_value/(1+rate)**terminal_horizon
    ev=pv_exp+pv_terminal
    br=equity_bridge(data,forecast,wacc,scenario)
    equity=ev+br['scenario_bridge']
    price=equity*1_000_000/wacc['shares']
    market_price=data['bridge']['price']
    return dict(scenario=scenario,wacc=rate,terminal_growth=g,terminal_roic=roic,explicit_pv=pv_exp,terminal_ebit=terminal_ebit,terminal_nopat=terminal_nopat,terminal_reinvestment_rate=re_rate,terminal_fcff=terminal_fcff,terminal_value=terminal_value,terminal_horizon=terminal_horizon,terminal_pv=pv_terminal,enterprise_value=ev,terminal_fraction=pv_terminal/ev if ev else 0,equity_value=equity,per_share=price,upside=price/market_price-1,cashflows=cashflows,bridge=br,forecast=forecast)

def peer_multiples(data:dict, hist:dict, bridge:dict, shares:float)->list[dict]:
    rows=[]
    eb=hist['ttm']['normalized_ebit'];eda=hist['ttm']['normalized_ebitda']
    for peer in data['peers']:
        p=deepcopy(peer)
        required=('price','shares_m','cash','debt','leases','other_ev_adjustment','ebit','da')
        complete=all(isinstance(p.get(f),(int,float)) for f in required)
        p['complete']=complete
        p['validated']=p.get('confidence')=='YES' # Historical source flag, independent of user certification
        price_date=p.get('market_price_date','')
        period_end=p.get('financial_period_end','')
        def valid_asof(value):
            try:
                return bool(value) and date.fromisoformat(str(value)) <= VAL_DATE
            except (TypeError,ValueError):
                return False
        p['multiple_approved']=bool(complete and p.get('user_validated') and p.get('accounting_reviewed') and p.get('comparability_reviewed')
            and str(p.get('source_url','')).startswith('https://') and len(str(p.get('adjustment_memo','')).strip())>=25
            and valid_asof(price_date) and valid_asof(period_end)
            and p.get('ebit',0)>0 and p.get('da',0)>=0)
        if complete:
            p['market_cap']=p['price']*p['shares_m']
            p['enterprise_value']=p['market_cap']-p['cash']+p['debt']+p['leases']+p['other_ev_adjustment']
            p['ebitda']=p['ebit']+p['da']
            p['ev_ebitda']=p['enterprise_value']/p['ebitda'] if p['ebitda']>0 else None
            p['ev_ebit']=p['enterprise_value']/p['ebit'] if p['ebit']>0 else None
            p['smsm_indication_ebitda']=(p['ev_ebitda']*eda+bridge['base_bridge'])*1_000_000/shares if p['ev_ebitda'] is not None and eda is not None else None
            p['smsm_indication_ebit']=(p['ev_ebit']*eb+bridge['base_bridge'])*1_000_000/shares if p['ev_ebit'] is not None and eb is not None else None
        else:
            for f in ('market_cap','enterprise_value','ebitda','ev_ebitda','ev_ebit','smsm_indication_ebitda','smsm_indication_ebit'):p[f]=None
        rows.append(p)
    return rows

def method_and_recommendation(data:dict, dcfs:dict, peers:list[dict],warnings:list[str])->dict:
    center=dcfs['Base']['per_share'];bear=dcfs['Bear']['per_share'];bull=dcfs['Bull']['per_share']
    approved=[p for p in peers if p.get('multiple_approved') and p.get('smsm_indication_ebitda') is not None]
    base=dict(method='DCF primary; relative cross-check',relative_publishable=False,final_recommendation='WITHHELD',
        rationale='Fewer than two source-reviewed comparable companies are approved; unresolved share count and economic-claim proxies remain.',
        conditional_market_view=('Below Base intrinsic indication' if data['bridge']['price']<center else 'Above Base intrinsic indication'),
        central=center,fair_range=[min(bear,bull),max(bear,bull)],central_published=False,relative_range=None,relative_median=None,accepted_peers=[p['ticker'] for p in approved])
    if len(approved)<2:return base
    indications=sorted(float(p['smsm_indication_ebitda']) for p in approved)
    n=len(indications);med=(indications[(n-1)//2]+indications[n//2])/2
    dispersion=(indications[-1]-indications[0])/med if med>0 else float('inf')
    base.update(relative_publishable=True,relative_range=[indications[0],indications[-1]],relative_median=med)
    if dispersion>.40 or abs(med/center-1)>.40:
        base['rationale']='Peer indications are reviewed but differ too widely from each other or the DCF (>40%); reconcile fundamentals before publishing an investment recommendation.'
        warnings.append('Validated peer/DCF dispersion threshold breached; final investment recommendation remains withheld.')
        return base
    lower,upper=sorted((bear,bull)); price=data['bridge']['price']; margin=.15
    if price<lower*(1-margin):rec='BUY (conditional)'
    elif price>upper*(1+margin):rec='SELL (conditional)'
    else:rec='HOLD / REVIEW'
    base.update(final_recommendation=rec,central_published=True,rationale='At least two documentary-reviewed peers; ≤40% peer dispersion and peer/DCF divergence; 15% safety margin tested against scenario range.')
    return base

def run_model(data:dict)->dict:
    """Complete valuation pass. Never mutates data. Blocks critical failures, flags provisional claims."""
    errors,warnings=validate_inputs(data)
    if errors:return dict(status='BLOCKED',errors=errors,warnings=warnings)
    try:
        w=calculate_wacc(data)
        hist=historical_view(data)
        cases={name:calculate_dcf(data,name,w) for name in ('Bear','Base','Bull')}
        if not (cases['Bear']['per_share']<=cases['Base']['per_share']<=cases['Bull']['per_share']):
            warnings.append('Scenario ordering is not monotonic: review growth/margin/reinvestment and WACC assumptions.')
        peers=peer_multiples(data,hist,cases['Base']['bridge'],w['shares'])
        rec=method_and_recommendation(data,cases,peers,warnings)
        return dict(status='PROVISIONAL',errors=[],warnings=warnings,wacc=w,historical=hist,dcf=cases,peers=peers,decision=rec,market=dict(price=data['bridge']['price'],market_cap=w['market_cap'],shares=w['shares']))
    except (ModelError,ZeroDivisionError,ValueError,KeyError,TypeError,OverflowError) as e:
        return dict(status='BLOCKED',errors=[str(e)],warnings=warnings)

def sensitivity(data:dict, kind:str, row_factors:list[float]|None=None, col_factors:list[float]|None=None)->dict:
    """Calculate actual full-engine sensitivity for Base case; not final-value scalars."""
    row_factors=row_factors if row_factors is not None else [-.01,-.005,0,.005,.01]
    col_factors=col_factors if col_factors is not None else [-.01,-.005,0,.005,.01]
    result=[]
    for ra in row_factors:
        row=[]
        for cb in col_factors:
            d=deepcopy(data)
            try:
                if kind=='WACC × terminal g':
                    w=calculate_wacc(d)
                    val=calculate_dcf(d,'Base',w,wacc_override=w['wacc']+ra,terminal_growth_override=d['scenarios']['Base']['terminal_growth']+cb)['per_share']
                else:
                    a=d['scenarios']['Base']
                    if kind=='Growth × EBIT margin':a['fy2027_growth']+=ra;a['fy2026_ebit_margin']+=cb;a['terminal_ebit_margin']+=cb
                    elif kind=='CapEx × NWC intensity':a['capex_revenue']+=ra;a['fy2026_nwc_revenue']+=cb;a['fy2031_nwc_revenue']+=cb
                    elif kind=='NCI × excess cash':a['nci_multiple']+=ra;a['cash_rollforward_extra']+=cb*1_000_000
                    else:raise ModelError('Unknown sensitivity type')
                    res=run_model(d)
                    if res['status']=='BLOCKED':raise ModelError('; '.join(res['errors']))
                    val=res['dcf']['Base']['per_share']
                row.append(val)
            except (ModelError,ZeroDivisionError):row.append(None)
        result.append(row)
    return dict(kind=kind,row_factors=row_factors,col_factors=col_factors,values=result)
