"""Mock Streamlit smoke tests. Exercise all six page branches without a browser.
These do NOT establish a live Streamlit session; require a separate local launch.
"""
from __future__ import annotations
import runpy,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
PAGES=['Dashboard & Overview','Historical Financial Data','Forecast Assumptions','Valuation Results','Scenarios & Sensitivity','Sources, Validation & Export']

class MockSession(dict):
    def __getattr__(self,name):return self[name]
    def __setattr__(self,name,value):self[name]=value

class FakeStreamlit:
    def __init__(self,page='Dashboard & Overview',state=None):
        self.page=page
        self.session_state=MockSession() if state is None else state
        self.sidebar=self
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def columns(self,n,**kwargs):return [self]*(len(n) if isinstance(n,list) else n)
    def radio(self,label,options,**kwargs):return self.page
    def selectbox(self,label,options,index=0,**kwargs):return list(options)[index]
    def number_input(self,label,value=0,**kwargs):return value
    def checkbox(self,label,value=False,**kwargs):return value
    def text_input(self,label,value='',**kwargs):return value
    def text_area(self,label,value='',**kwargs):return value
    def file_uploader(self,*args,**kwargs):return None
    def button(self,*args,**kwargs):return False
    def download_button(self,*args,**kwargs):return False
    def expander(self,*args,**kwargs):return self
    def stop(self):raise RuntimeError('app was blocked unexpectedly')
    def rerun(self):raise RuntimeError('unexpected rerun')
    def __getattr__(self,key):
        # Presentation-only primitives are no-ops in the mock.
        if key.startswith('__'):raise AttributeError(key)
        return lambda *a,**k:None

@pytest.mark.parametrize('page',PAGES)
def test_each_streamlit_page_executes_with_mock(monkeypatch,page):
    fake=FakeStreamlit(page)
    monkeypatch.setitem(sys.modules,'streamlit',fake)
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
    assert fake.session_state['input_data']['company']=='SMSM'
