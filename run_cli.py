"""Standalone reference-engine execution; works without Streamlit."""
import json
from pathlib import Path
from valuation.engine import run_model
from valuation.exports import report_json
root=Path(__file__).resolve().parent
inputs=json.loads((root/'data'/'reference_inputs.json').read_text(encoding='utf-8'))
result=run_model(inputs)
if result['status']=='BLOCKED':
    raise SystemExit('BLOCKED: '+ '; '.join(result['errors']))
for case,v in result['dcf'].items():
    print(f"{case}: Rp {v['per_share']:,.2f} / share | EV Rp {v['enterprise_value']/1000:,.1f} bn")
print('WACC:',f"{result['wacc']['wacc']:.6%}")
print('Recommendation:',result['decision']['final_recommendation'])
out=root/'SMSM_cli_valuation_results.json';out.write_bytes(report_json(result,inputs))
print('Report:',out)
