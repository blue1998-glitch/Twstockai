"""Read-only actual DAY1 owner/UI verification; no permanent listener.

Configuration, credentials, screenshots and exact downloads stay outside Git.
Never capture providers or invoke the recognition/indicator engines here.
"""
import base64, hashlib, json, re, subprocess, threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import Counter
from rotation_research import artifact_codec as codec
from rotation_research.private_portability import private
from rotation_research.store import Journal
from graph_core_chart.mobile_private import make_server
from graph_core.day1_20261103.apply_once import file_state


def verify(root, work):
    root=private(root);work=private(work)
    before=file_state(root)
    head=json.loads((root/'current-increment-run.json').read_bytes())
    batch=Journal(root/'runs').read(head['id'])['value']
    page=Path(head['private_preview']['path'])
    raw=codec.read_bytes(page,expected_sha=head['private_preview']['sha256'],expected_bytes=head['private_preview']['bytes'])
    state=json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)[1]);del raw
    rows={x['identity']:x for x in state['stocks']}
    assert len(rows)==batch['summary']['processed']
    for row in state['stocks']:
        assert row['as_of']==batch['as_of']
        for k in ('execution_qualified','historical_signal_eligible','policy_authorized'):assert row[k] is False
        assert row['primary_pressure_id'] is None and row['imputed_close'] is None and row['valuation'] is None
    cases=[]
    for name in ('early-prefix-proof-private.json','tpex-prefix-proof-private.json'):
        for evidence in json.loads((work/name).read_bytes())['checks']:
            row=rows[evidence['identity']]
            assert row['status']=='SEGMENTED_RESEARCH'
            cases.append(dict(row,result_id=evidence['result_id'],chart_path=str(page.parent/row['preview_series']['path'])))
    old=json.loads(private('/workspace/twstockai-local-data/real1_20261102/connection-private.json').read_bytes())
    credential=private(old['credential_file'])
    server=make_server(None,credential,head=root/'current-increment-run.json')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin='http://127.0.0.1:'+str(server.server_port)
    basic='Basic '+base64.b64encode((old['auth']['username']+':'+old['auth']['password']).encode()).decode()
    checks=[]
    def request(path,*,auth=True,headers=None,method='GET',expected=200,fingerprint=None):
        h={'Authorization':basic} if auth else {};h.update(headers or {})
        try:r=urlopen(Request(origin+path,headers=h,method=method),timeout=180)
        except HTTPError as error:r=error
        with r:
            assert r.status==expected,(path,r.status,expected)
            digest=hashlib.sha256();size=0
            while True:
                part=r.read(1024*1024)
                if not part:break
                digest.update(part);size+=len(part)
            if fingerprint:assert (size,digest.hexdigest())==(fingerprint['bytes'],fingerprint['sha256'])
        checks.append(dict(kind='owner_http',status=expected,fingerprint_checked=bool(fingerprint)))
    output=work/'browser-first';output.mkdir(mode=0o700,exist_ok=False)
    try:
        catalogue=json.loads(Path(head['batch_index']).read_bytes())
        assert [v['as_of'] for v in catalogue['batches']]==[batch['as_of'],Journal(root/'runs').read(batch['parent_run'])['value']['as_of']]
        address='/batch-'+head['private_preview']['sha256']+'/'+page.name
        request('/batches',auth=False,expected=401)
        request('/batches')
        request(address,fingerprint=head['private_preview'])
        request('/raw/private',expected=404)
        request('/batches',headers={'Origin':'https://unauthorized.invalid'},expected=403)
        request('/batches',method='POST',expected=405)
        prior=catalogue['batches'][1]
        request('/batch-'+prior['sha256']+'/'+Path(prior['path']).name,fingerprint=prior)
        event_stock=next(s for s in cases if state['radar'].get(s['identity'],{}).get('events'))
        gap=Journal(root/'results').read(cases[0]['result_key'])['value']['result']['data_gaps']
        cfg=dict(auth=old['auth'],origin=origin,url=origin+address,expected=len(rows),charts=sum(bool(s.get('preview_series')) for s in rows.values()),
            as_of=batch['as_of'],terminal_counts=batch['summary']['terminal_counts'],compare=cases,
            short=next(s for s in rows.values() if s['status']=='INSUFFICIENT_HISTORY' and s.get('preview_series')),
            event_case=event_stock,event_stocks=sum(bool(x.get('events')) for x in state['radar'].values()),event_records=sum(len(x.get('events',[])) for x in state['radar'].values()),
            refused=[next(s for s in rows.values() if s['status']==k) for k in ('MISSING_QUOTE','DATA_QUALITY_FAILURE')],
            gap_case=dict(cases[0],data_gaps=gap,query_date=None))
        config=work/'connection-day1-private.json';codec.immutable(config,codec.encoded(cfg))
        del state
        code=Path(__file__).with_name('test_new_day_ui.cjs')
        p=subprocess.run(['node',str(code),str(config),str(output)],capture_output=True,text=True)
        codec.immutable(work/'browser-first.stdout.log',p.stdout.encode());codec.immutable(work/'browser-first.stderr.log',p.stderr.encode())
        report=dict(status='PASS' if p.returncode==0 else 'FAIL',node_returncode=p.returncode,owner_http=checks,
            event_records=cfg['event_records'],event_stocks=cfg['event_stocks'],as_of=batch['as_of'],charts=cfg['charts'],
            original_catalogue_retained=True,new_source_fetches=0,core_calls=0,permanent_listener=False,android='NOT_TESTED_NEW_BUILD')
        codec.immutable(work/'ui-verification-private.json',codec.encoded(report))
        print(json.dumps(report),flush=True)
        if p.returncode:raise RuntimeError('ACTUAL_NEW_DAY_BROWSER_FAILED_SEE_PRIVATE_LOG')
    finally:
        server.shutdown();server.server_close();thread.join(timeout=10)
        assert file_state(root)==before,'READONLY_UI_CHANGED_SAVED_SOURCE'


if __name__=='__main__':
    import sys
    verify(sys.argv[1],sys.argv[2])
