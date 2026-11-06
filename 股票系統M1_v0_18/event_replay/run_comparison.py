"""Offline recorded-source audit and three-scenario engine replay."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'event_replay';RAW=HERE/'raw';OUT=HERE/'output'
sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError,number
from event_replay import parse_contract_notice,run_event_replay


def captured(path):
    b=path.read_bytes();m=json.loads(path.with_name(path.name+'.meta.json').read_text())
    if hashlib.sha256(b).hexdigest()!=m['sha256'] or len(b)!=m['bytes']:
        raise DataError('CAPTURE_HASH','source','Saved source differs from capture metadata')
    return b,m


def reviewed_events(code,job):
    events=json.loads((ROOT/'data'/f'{code}_events.json').read_text())
    with zipfile.ZipFile(ROOT/'upstream/M0_7_長期日線與還原候選_v0_2.zip') as z:
        for e in events:
            b=z.read('原始證據/'+e['source_file'])
            if hashlib.sha256(b).hexdigest()!=e['source_sha256']:raise DataError('REPLAY_SOURCE_HASH','source','Upstream captured source mismatch')
            p=json.loads(b);t=p['tables'][0];rows=[dict(zip(t['fields'],r)) for r in t['data']]
            found=[r for r in rows if r['代號']==code and r['除權息日期']==f"{int(e['effective_date'][:4])-1911}/{e['effective_date'][5:7]}/{e['effective_date'][8:]}" ]
            if len(found)!=1:raise DataError('REPLAY_SOURCE_ROW','row','Unique official event row required')
            r=found[0]
            if r['權/息']!='除息' or number(r['每仟股無償配股'],'stock')!=0 or number(r['現金增資股數'],'capital')!=0:
                raise DataError('UNSUPPORTED_CORPORATE_ACTION','row','Only archived cash-only events are allowed')
            for key,col in [('cash_dividend','現金股利'),('previous_close','除權息前收盤價'),('official_reference','除權息參考價')]:
                if number(e[key],key)!=number(r[col],col):raise DataError('REPLAY_SOURCE_ROW','row','Archived event differs from official row')
    return events


def main():
    OUT.mkdir(exist_ok=True);notices=[];attempts=[]
    issuer_facts={x['fact']['code']:x['fact'] for x in json.loads((ROOT/'event_audit/output/事件證據與啟用檢查.json').read_text())['corporate_actions']}
    for code in ['1101','2884']:
        pdf,pm=captured(RAW/f'taifex_{code}_20260701.pdf')
        if pm.get('status')!=200 or pm['url']!=f'https://www.taifex.com.tw/file/taifex/CHINESE/11/attach/{code}_20260701.pdf' or not pdf.startswith(b'%PDF'):
            raise DataError('PDF_SOURCE','pdf','Official recorded PDF response required')
        text,tm=captured(RAW/f'taifex_{code}_20260701.txt')
        notice=parse_contract_notice(text.decode(),code=code);notice['source_record']=pm;notice['text_derivation']=tm
        if number(notice['cash_per_share'],'PDF cash')!=number(issuer_facts[code]['cash_per_share'],'issuer cash'):
            raise DataError('CASH_EVIDENCE_CONFLICT','cash','Issuer page and contract notice differ')
        notice['issuer_cash_crosscheck']='MATCH'
        # The stored monthly source marks the ex-day change as X0.00. This is
        # explicitly not usable as numeric zero to reconstruct a reference.
        month=json.loads((ROOT/'data_audit/raw'/f'{code}_202607.json').read_text());fields=month['fields'];row=month['data'][0]
        marker=dict(zip(fields,row))['漲跌價差']
        if marker!='X0.00':raise DataError('UNREVIEWED_CHANGE_MARKER','漲跌價差','Reviewed monthly marker changed')
        notice.update(monthly_change_marker=marker,reference_from_monthly_change='BLOCKED_NON_NUMERIC_MARKER',
                      engine_ready=False,remaining_requirements=(['STOCK_EX_DATE_DIRECT_EVIDENCE'] if code=='2884' else [])+['STOCK_REFERENCE_PRICE_CROSSCHECK','COMPLETE_PERIOD_ACTION_COVERAGE_UNVERIFIED'])
        notices.append(notice)
    (OUT/'補充官方契約證據.json').write_text(json.dumps(notices,ensure_ascii=False,indent=2))
    for p in sorted(RAW.glob('*.meta.json')):attempts.append(dict(file=p.name[:-10],**json.loads(p.read_text())))
    (HERE/'來源擷取清單.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2))
    reports=[]
    for code in ['8069','6488']:
        job=json.loads((ROOT/'data'/f'{code}_analysis_job.json').read_text());events=reviewed_events(code,job)
        bundle=run_event_replay(job,events)
        (HERE/f'{code}_重播工作單組.json').write_text(json.dumps(bundle['jobs'],ensure_ascii=False,indent=2))
        for name,result in bundle['results'].items():
            (OUT/f'{code}_{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        report=bundle['report'];report['request_fingerprint']=bundle['request_fingerprint'];reports.append(report)
        print(code,report['status'],len(report['checks']),'checks',flush=True)
    (OUT/'事件重播比較驗收.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
    if any(r['status']!='PASS' for r in reports):raise SystemExit(1)

if __name__=='__main__':main()
