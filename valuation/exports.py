"""Download outputs generated from the same model result used by the dashboard."""
from __future__ import annotations
import csv,html,io,json
from datetime import datetime,timezone

def compact_report(result:dict,data:dict)->dict:
    return {
        'company':'PT Selamat Sempurna Tbk (IDX: SMSM)',
        'valuation_date':data['valuation_date'],
        'generated_utc':datetime.now(timezone.utc).isoformat(),
        'financial_units':'IDR million; price in IDR/share',
        'model_status':result['status'],
        'market_price':result['market']['price'],
        'market_cap_rp_m':result['market']['market_cap'],
        'wacc':result['wacc']['wacc'],
        'scenarios':{k:{'per_share':v['per_share'],'upside':v['upside'],'enterprise_value_rp_m':v['enterprise_value'],'parent_equity_rp_m':v['equity_value'],'explicit_fcff_pv':v['explicit_pv'],'terminal_value_pv':v['terminal_pv'],'terminal_share':v['terminal_fraction']} for k,v in result['dcf'].items()},
        'peer_multiples':[{k:p.get(k) for k in ('ticker','currency','ev_ebitda','ev_ebit','complete','multiple_approved','smsm_indication_ebitda','smsm_indication_ebit')} for p in result['peers']],
        'recommendation':result['decision']['final_recommendation'],
        'recommendation_reason':result['decision']['rationale'],
        'warnings':result['warnings']
    }

def report_json(result:dict,data:dict)->bytes:
    return json.dumps(compact_report(result,data),ensure_ascii=False,indent=2).encode('utf-8')

def report_csv(result:dict,data:dict)->bytes:
    f=io.StringIO();w=csv.writer(f)
    w.writerow(['SMSM valuation scenario','Per-share IDR','Upside','Operating EV Rp million','Parent equity Rp million','Terminal fraction'])
    for k,v in result['dcf'].items():w.writerow([k,round(v['per_share'],4),round(v['upside'],7),round(v['enterprise_value'],4),round(v['equity_value'],4),round(v['terminal_fraction'],7)])
    w.writerow(['Status',result['decision']['final_recommendation']])
    return f.getvalue().encode('utf-8-sig')

def report_html(result:dict,data:dict)->bytes:
    rep=compact_report(result,data)
    rows=''.join('<tr><td>'+html.escape(k)+'</td><td>Rp '+format(v['per_share'],',.2f')+'</td><td>'+format(v['upside'],'.2%')+'</td><td>'+format(v['enterprise_value'],',.0f')+'</td></tr>' for k,v in result['dcf'].items())
    warn=''.join('<li>'+html.escape(x)+'</li>' for x in rep['warnings'])
    out=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>SMSM Valuation – {rep['valuation_date']}</title>
    <style>body{{font-family:Arial,sans-serif;color:#243448;max-width:920px;margin:42px auto;line-height:1.5}}h1{{color:#142E4C}}table{{border-collapse:collapse;width:100%}}th{{background:#15314E;color:white;text-align:left}}th,td{{border-bottom:1px solid #ccd8e4;padding:12px}}.label{{font-weight:bold}}.risk{{background:#f4f7fb;padding:18px;border-radius:8px}}@media print{{body{{margin:15mm}}}}</style>
    <h1>PT Selamat Sempurna Tbk · SMSM</h1><p>Valuation date: {rep['valuation_date']} · Generated UTC: {html.escape(rep['generated_utc'])}</p>
    <p>Market close: Rp {rep['market_price']:,.0f} per share · WACC {rep['wacc']:.3%} · Model status: {rep['model_status']}</p>
    <h2>FCFF / WACC scenarios</h2><table><thead><tr><th>Scenario</th><th>Intrinsic Rp/share</th><th>Implied upside</th><th>Operating EV Rp million</th></tr></thead><tbody>{rows}</tbody></table>
    <h2>Recommendation control</h2><p><strong>{html.escape(rep['recommendation'])}</strong> — {html.escape(rep['recommendation_reason'])}</p>
    <div class="risk"><strong>Provisional information and risks</strong><ul>{warn}</ul></div><p>All results are condition-dependent analyst model estimates, not audited future figures.</p>
    </html>'''
    return out.encode('utf-8')
