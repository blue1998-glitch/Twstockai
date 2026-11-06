"""Reproduce v0.7 evidence staging using captured sources; no network."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'event_audit';RAW=HERE/'raw'
sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError
from event_evidence import parse_tpex_reviewed_closure,parse_tcc_dividend,parse_esun_dividend,stage_cash_factor


def source(name,expected_url):
    b=(RAW/name).read_bytes();m=json.loads((RAW/(name+'.meta.json')).read_text())
    if m.get('status')!=200 or m.get('url')!=expected_url or m.get('sha256')!=hashlib.sha256(b).hexdigest() or m.get('bytes')!=len(b):
        raise DataError('SOURCE_PROVENANCE','source','Captured response hash, URL, length or status mismatch')
    return b.decode('utf-8'),dict(file='event_audit/raw/'+name,**m)


def main():
    out=HERE/'output';out.mkdir(exist_ok=True)
    text,meta=source('tpex_press_20260709.json','https://www.tpex.org.tw/www/zh-tw/news/list?startDate=2026/07/09&endDate=2026/07/10&response=json')
    closure=parse_tpex_reviewed_closure(json.loads(text));closure.update(source_url=meta['url'],source_record=meta,
        detail_retrieval='Web detail fetch returned 403; no detail-body claim. Official list supplies full reviewed title.')
    old=json.loads((HERE/'v0_6_臨時休市證據.json').read_text())
    (ROOT/'data_audit/臨時休市證據.json').write_text(json.dumps(old+[closure],ensure_ascii=False,indent=2))
    facts=[]
    for name,url,parser in [
        ('tcc_dividends.html','https://www.tccgroupholdings.com/dividend',parse_tcc_dividend),
        ('esun_shareholders.html','https://www.esunfhc.com/zh-tw/investor-relations/shareholders/shareholder-Information',parse_esun_dividend)]:
        text,meta=source(name,url);fact=parser(text);fact['source_record']=meta
        candles=json.loads((ROOT/'data_audit'/f"{fact['code']}_candles.json").read_text())
        facts.append(dict(fact=fact,staging=stage_cash_factor(fact,candles)))
    report=dict(schema_version='event-evidence/0.1',closure=closure,corporate_actions=facts,
                complete_period_coverage='UNVERIFIED',engine_input_changes='NONE; staged facts not forwarded',
                evidence_scope='Individual current-source facts only; not complete historical point-in-time certification')
    (out/'事件證據與啟用檢查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    manifest=[]
    for p in sorted(RAW.glob('*.meta.json')):manifest.append(dict(name=p.name[:-10],**json.loads(p.read_text())))
    (HERE/'來源擷取清單.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    for item in facts:print(item['fact']['code'],item['staging']['status'],item['staging']['blocked_reasons'])
    print('TPEX verified single closure case:',closure['date'])

if __name__=='__main__':main()
