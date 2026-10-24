"""Controlled Excel reader implemented using the Python standard library.
Reads *hardcoded* input cells only, never depends on stale formula-cache results.
Supports the two exact documented Stage 2B / Stage 4 templates.
"""
from __future__ import annotations
from copy import deepcopy
from io import BytesIO
import posixpath
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL='{http://schemas.openxmlformats.org/package/2006/relationships}'

class WorkbookImportError(ValueError):pass

class XlsxInputReader:
    def __init__(self, source:bytes):
        if not source or len(source)>15_000_000:raise WorkbookImportError('Upload must be a nonempty .xlsx under 15 MB')
        try:self.z=ZipFile(BytesIO(source))
        except BadZipFile as e:raise WorkbookImportError('File is not a valid .xlsx ZIP container') from e
        names=set(self.z.namelist())
        if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names:raise WorkbookImportError('Not an Excel .xlsx file')
        if any(i.file_size>20_000_000 for i in self.z.infolist()):raise WorkbookImportError('Excessively large worksheet detected')
        try:
            root=ET.fromstring(self.z.read('xl/workbook.xml'))
            rel=ET.fromstring(self.z.read('xl/_rels/workbook.xml.rels'))
            targets={e.attrib['Id']:e.attrib['Target'] for e in rel if e.attrib.get('Target')}
            self.paths={}
            for s in root.findall('s:sheets/s:sheet',NS):
                rid=s.attrib[f'{{{NS["r"]}}}id'];target=targets[rid]
                path=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
                if path not in names:raise WorkbookImportError(f'Missing worksheet XML for {s.attrib["name"]}')
                self.paths[s.attrib['name']]=path
            self.strings=[]
            if 'xl/sharedStrings.xml' in names:
                sr=ET.fromstring(self.z.read('xl/sharedStrings.xml'))
                for si in sr.findall('s:si',NS):
                    self.strings.append(''.join(t.text or '' for t in si.findall('.//s:t',NS)))
        except (ET.ParseError,KeyError,IndexError) as e:
            raise WorkbookImportError(f'Malformed Excel workbook metadata: {e}') from e
        self.cache={}
    def sheet(self,name):
        if name not in self.paths:raise WorkbookImportError(f'Required worksheet missing: {name}')
        if name not in self.cache:
            root=ET.fromstring(self.z.read(self.paths[name]));sheet={}
            for cell in root.findall('.//s:sheetData/s:row/s:c',NS):
                address=cell.attrib.get('r'); typ=cell.attrib.get('t','n')
                # We explicitly skip formula cells. They must be recalculated in pure Python.
                if cell.find('s:f',NS) is not None:continue
                val=cell.find('s:v',NS)
                if typ=='inlineStr':
                    text=''.join(e.text or '' for e in cell.findall('.//s:t',NS))
                    sheet[address]=text
                elif val is not None and val.text is not None:
                    if typ=='s':sheet[address]=self.strings[int(val.text)]
                    elif typ in ('str','e'):sheet[address]=val.text
                    elif typ=='b':sheet[address]=val.text=='1'
                    else:
                        n=float(val.text);sheet[address]=int(n) if n.is_integer() else n
            self.cache[name]=sheet
        return self.cache[name]
    def input(self,sheet,addr,required=False):
        x=self.sheet(sheet).get(addr)
        if required and not isinstance(x,(int,float)):
            raise WorkbookImportError(f'Missing hardcoded input {sheet}!{addr}; formulas are not accepted as uploaded source inputs')
        return x

S4_ASS={7:'fy2026_growth',8:'fy2027_growth',9:'growth_fade',10:'fy2026_ebit_margin',11:'terminal_ebit_margin',12:'tax_rate',13:'da_revenue',14:'capex_revenue',15:'fy2026_nwc_revenue',16:'fy2031_nwc_revenue',17:'terminal_growth',18:'terminal_roic',19:'wacc_shift',20:'nci_multiple',21:'operating_cash_reserve_revenue',22:'cash_rollforward_extra',23:'derivative_liability_fraction'}
S4_CAP={7:'sovereign_yield',8:'sovereign_spread',10:'indonesia_total_erp',11:'country_erp',13:'domestic_exposure',15:'unlevered_beta',17:'bank_debt',18:'lease_debt',19:'nci_equity_weight_proxy',20:'bank_debt_cost',21:'lease_debt_cost',22:'debt_tax_shield'}
S4_BR={6:'price',8:'issued_shares',9:'treasury_adjustment',13:'bank_debt',14:'lease_debt',15:'nci_book',16:'associate_book',17:'other_investments_book',18:'cash',19:'term_deposits',20:'derivative_liability',21:'dividend_july_per_share',22:'dividend_aug_per_share',24:'days_in_year'}
S2_HIST={7:'revenue',8:'ebit',9:'consolidated_net_income',10:'parent_net_income',11:'income_tax',12:'operating_cash_flow',13:'ppe_depreciation',14:'rou_depreciation',15:'amortization',16:'ppe_cash_purchases',17:'capital_advances_cash',18:'intangible_cash'}

def update_from_workbook(source:bytes, baseline:dict)->tuple[dict,dict]:
    r=XlsxInputReader(source);d=deepcopy(baseline)
    audit={'kind':None,'changed':[],'notes':[]}
    if '03 Forecast Assumptions' in r.paths and '08 Equity Bridge' in r.paths:
        audit['kind']='Stage4 valuation model'
        for c,sc in [('B','Bear'),('C','Base'),('D','Bull')]:
            for row,key in S4_ASS.items():
                v=r.input('03 Forecast Assumptions',f'{c}{row}',True)
                if d['scenarios'][sc][key]!=v:audit['changed'].append(f'{sc}.{key}')
                d['scenarios'][sc][key]=v
        for row,key in S4_CAP.items():
            v=r.input('06 Cost of Equity & WACC',f'B{row}',True)
            if d['cost_of_capital'][key]!=v:audit['changed'].append(f'cost_of_capital.{key}')
            d['cost_of_capital'][key]=v
        for row,key in S4_BR.items():
            v=r.input('08 Equity Bridge',f'B{row}',True)
            if d['bridge'][key]!=v:audit['changed'].append(f'bridge.{key}')
            d['bridge'][key]=v
        for idx,row in enumerate((6,7,8)):
            for col,key in [('C','price'),('D','shares_m'),('E','cash'),('F','debt'),('G','leases'),('H','other_ev_adjustment'),('I','ebit'),('J','da')]:
                v=r.input('09 Comparable Companies',f'{col}{row}',False)
                if d['peers'][idx].get(key)!=v:audit['changed'].append(f"peer.{d['peers'][idx]['ticker']}.{key}")
                d['peers'][idx][key]=v
        audit['notes'].append('Stage4 derived historic H1, EBITDA and TTM caches are ignored; corrected Stage2B historical inputs retained.')
    elif '02 Historical Financials' in r.paths and '04 Working Capital' in r.paths:
        audit['kind']='Stage2B reconciled financial data'
        for y,c in [(2021,'B'),(2022,'C'),(2023,'D'),(2024,'E'),(2025,'F')]:
            hist=next(x for x in d['historical'] if x['year']==y)
            for row,key in S2_HIST.items():
                v=r.input('02 Historical Financials',f'{c}{row}',key!='intangible_cash')
                if hist.get(key)!=v:audit['changed'].append(f'{y}.{key}')
                hist[key]=v
        def calculated_nwc(col):
            assets=sum(r.input('04 Working Capital',f'{col}{row}',True) for row in range(7,15))
            liabilities=sum(r.input('04 Working Capital',f'{col}{row}',True) for row in range(17,25))
            return assets-liabilities
        for year,col in [(2023,'C'),(2024,'D'),(2025,'E')]:
            v=calculated_nwc(col)
            rec=next(x for x in d['historical'] if x['year']==year)
            if rec.get('nwc')!=v:audit['changed'].append(f'{year}.nwc')
            rec['nwc']=v
        for year in (2023,2024,2025):
            prior=(1650274 if year==2023 else next(x['nwc'] for x in d['historical'] if x['year']==year-1))
            rec=next(x for x in d['historical'] if x['year']==year)
            rec['delta_nwc']=rec['nwc']-prior
        for row,key in S2_HIST.items():
            v=r.input('02 Historical Financials',f'G{row}', key!='intangible_cash')
            if d['interim']['2026H1'].get(key)!=v:audit['changed'].append(f'H1_2026.{key}')
            d['interim']['2026H1'][key]=v
        d['interim']['2026H1']['da']=sum(d['interim']['2026H1'][k] for k in ('ppe_depreciation','rou_depreciation','amortization'))
        nwc26=calculated_nwc('F')
        d['interim']['2026H1']['nwc']=nwc26
        d['interim']['2026H1']['delta_nwc']=nwc26-next(x['nwc'] for x in d['historical'] if x['year']==2025)
        for year,col in [(2024,'B'),(2025,'C')]:
            v=r.input('05 CapEx & Reinvestment',f'{col}7',True)
            rec=next(x for x in d['historical'] if x['year']==year)
            if rec.get('gross_ppe_additions')!=v:audit['changed'].append(f'{year}.gross_ppe_additions')
            rec['gross_ppe_additions']=v
        d['interim']['2026H1']['gross_ppe_additions']=r.input('05 CapEx & Reinvestment','D7',True)
        cap={'cash':'E7','term_deposits':'E8','nci_book':'E14','associate_book':'E15','other_investments_book':'E16','derivative_liability':'E18','issued_shares':'E32','price':'E35'}
        for key,cell in cap.items():
            v=r.input('06 Capital Structure',cell,True)
            if d['bridge'][key]!=v:audit['changed'].append(f'bridge.{key}')
            d['bridge'][key]=v
        loans=sum(r.input('06 Capital Structure',f'E{x}',True) for x in (9,10,11))
        leases=sum(r.input('06 Capital Structure',f'E{x}',True) for x in (12,13))
        for key,value in [('bank_debt',loans),('lease_debt',leases)]:
            if d['bridge'][key]!=value:audit['changed'].append(f'bridge.{key}')
            d['bridge'][key]=value
            d['cost_of_capital'][key]=value
        d['cost_of_capital']['nci_equity_weight_proxy']=d['bridge']['nci_book']
        audit['notes'].append('Reported annual/interim hardcodes, NWC components, CapEx and H1 2026 capitalization inputs refreshed; Stage4 economic assumptions preserved.')
    else:
        raise WorkbookImportError('Unsupported workbook: expected original Stage2B or Stage4 sheet structure. Generic Excel tables are not accepted to avoid silent column misalignment.')
    return d,audit
