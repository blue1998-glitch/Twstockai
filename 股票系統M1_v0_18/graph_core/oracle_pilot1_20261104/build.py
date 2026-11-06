"""Reuse LITE1/core/viewer with existing synthetic fixtures only. No network."""
import argparse,hashlib,json,re,resource,shutil,tempfile,time,zipfile
from copy import deepcopy
from pathlib import Path
from graph_core.obs1_20261102.build_demo import fixture
from graph_core.core import analyze,fingerprint
from graph_core.market_preview import source_segment_ma
from graph_core_chart.build import display_ids
from graph_core_chart.evidence import layers
from graph_core.lite1_20261103.decision import project,empty,card
from graph_core.lite1_20261103.render import compile_view
from technical_chart.build import pack,unpack
from product_candidate.macd import macd,PARAMETERS
from rotation_research.store import Journal

HERE=Path(__file__).parent
PROJECT=HERE.parents[1]
VERSION='oracle-isolated-synthetic-pilot/0.1'
RESERVE=512*1024*1024
LIMIT=16*1024*1024
LABEL='合成測試資料／非真實交易訊號'

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def script_json(value):return encoded(value).decode().replace('<','\\u003c').replace('&','\\u0026')
def immutable(path,raw):
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('PILOT_IMMUTABLE_OUTPUT_CHANGED')
        return
    if shutil.disk_usage(path.parent).free<RESERVE+len(raw)+65536:raise OSError('PILOT_CAPACITY_REFUSED')
    with path.open('xb') as f:f.write(raw)

def make_states(work):
    _,batch=fixture(work)
    # Existing synthetic fixture dates, not a real exchange calendar.
    dates=sorted({b['date'] for s in batch['stocks'] if s.get('result_key') for b in Journal(work/'results').read(s['result_key'])['value']['input']['bars']})[-2:]
    mapping={};states={};snapshots=[]
    def packet(value):
        raw=encoded(value);name='series-'+sha(raw)+'.json';mapping[name]=raw.decode()
        return dict(path=name,bytes=len(raw),sha256=sha(raw))
    for day in dates:
        bid='SYNTHETIC-PILOT-'+day
        parent=fingerprint(dict(version=VERSION,synthetic=True,as_of=day))
        rows=[]
        for old in batch['stocks']:
            s={k:deepcopy(old[k]) for k in ['identity','code','name','market','status','result_key']}
            s['name']={'A':'合成甲','B':'合成乙','SHORT':'合成短史','NONE':'合成直行','REFUSED':'合成拒用'}[s['code']]
            s['as_of']=day
            if old.get('result_key'):
                p=deepcopy(Journal(work/'results').read(old['result_key'])['value']['input'])
                p['bars']=p['bars'][-40:]  # Small bounded tail of the EXISTING synthetic fixture.
                p['bars']=[b for b in p['bars'] if b['date']<=day]
                p['expected_dates']=[b['date'] for b in p['bars']]
                # A one-bar fixture starts later; keep explicit shortage at the earlier date.
                if not p['bars']:
                    s['status']='INSUFFICIENT_HISTORY';s['result_key']=None;d=empty(s)
                else:
                    r=analyze(p,as_of=day);bars=p['bars']
                    series=dict(code=s['code'],exchange=s['market'],source=dict(id=p['context']['source_id'],name=LABEL,role='SYNTHETIC_ENGINEERING_ONLY',historical_available_at='NOT_APPLICABLE_SYNTHETIC'),price_basis_id=p['context']['price_basis_id'],bars=bars,macd=macd([b['close'] for b in bars]),moving_averages=source_segment_ma(bars,[]),results=[r],presentations={day:display_ids(r)},manual_audits={},numeric_frame_ids={day:fingerprint(p)},source_gaps=dict(calendar_status='SYNTHETIC_SEQUENCE_NOT_MARKET_CALENDAR',actions_coverage='NOT_APPLICABLE_SYNTHETIC',historical_publication_timing='NOT_APPLICABLE_SYNTHETIC'),macd_parameters=PARAMETERS,input_bindings={day:dict(core_input_fingerprint=fingerprint(p),source_id=p['context']['source_id'],price_basis_id=p['context']['price_basis_id'],synthetic_only=True)},box_evidence={day:layers(r,bars)})
                    if unpack(pack(series))!=series:raise ValueError('SYNTHETIC_TRANSPORT_PRECISION_CHANGED')
                    s['preview_series']=packet(pack(series));d=project(s,r)
                    snapshots.append(dict(identity=s['identity'],as_of=day,input=p,series_descriptor=s['preview_series'],result_sha256=sha(encoded(r)),indicators_sha256=sha(encoded(dict(macd=series['macd'],moving_averages=series['moving_averages']))),decision=deepcopy(d)))
            else:d=empty(s)
            d.update(batch_id=bid,source_preview_sha256=parent)
            s.update(decision=card(d),decision_detail=packet(dict(schema='lite-decision/0.1',identity=s['identity'],as_of=day,decision=d)))
            rows.append(s)
        states[day]=dict(schema='private-lite-workbench/0.1',summary=dict(as_of=day,expected=len(rows),charts=sum(bool(s.get('preview_series')) for s in rows),status='SYNTHETIC_ONLY_NOT_MARKET',synthetic_demo=True),stocks=rows,radar_routes={},radar_dates=[],radar_types=[],batch_id=bid,source_preview_sha256=parent,synthetic_only=True)
    return states,mapping,snapshots

def build(output):
    out=Path(output).resolve()
    if out.exists():raise FileExistsError('NEW_ISOLATED_OUTPUT_REQUIRED')
    if shutil.disk_usage(out.parent).free<RESERVE+LIMIT:raise OSError('PILOT_CAPACITY_PREFLIGHT')
    started=time.monotonic();out.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix='pilot-fixture-',dir=out.parent) as td:
        states,mapping,snapshots=make_states(Path(td))
    latest=max(states);html,ui_sha=compile_view(states[latest],latest)
    text=html.decode()
    pre='<script id="pilot-states" type="application/json">'+script_json(states)+'</script><script id="synthetic-demo-series" type="application/json">'+script_json(mapping)+'</script><script>'+ (HERE/'date-init.js').read_text()+'</script>'
    text=text.replace('<script id="payload"',pre+'<script id="payload"',1)
    text=text.replace('</body>','<script>'+(HERE/'pilot.js').read_text()+'</script></body>')
    text=text.replace('</head>','<style>'+(HERE/'pilot.css').read_text()+'</style></head>')
    text=text.replace('<title>Twstockai 股票系統</title>','<title>Twstockai 股票系統｜合成測試版</title>')
    # Mark the otherwise unchanged original next-layer viewer wording as synthetic.
    text=text.replace('來源與公司行動依保存資格；跨來源不自動認證。',LABEL+'；未連接任何市場來源。')
    files={'Twstockai_SYNTHETIC_PILOT.html':text.encode(),'synthetic-snapshots.json':encoded(dict(version=VERSION,synthetic_only=True,snapshots=snapshots)),
      'serve.py':(HERE/'serve.py').read_bytes(),'README.txt':(HERE/'BUNDLE_README.txt').read_bytes(),
      'graph_core_chart/__init__.py':b'','graph_core_chart/mobile_private.py':(PROJECT/'graph_core_chart/mobile_private.py').read_bytes(),
      'rotation_research/__init__.py':b'','rotation_research/artifact_codec.py':(PROJECT/'rotation_research/artifact_codec.py').read_bytes()}
    files.update({name:raw.encode() for name,raw in mapping.items()})
    if sum(map(len,files.values()))>LIMIT//2:raise ValueError('PILOT_BUNDLE_SIZE_LIMIT')
    for name,raw in files.items():
        path=out/name;path.parent.mkdir(exist_ok=True);immutable(path,raw)
    manifest=dict(schema='synthetic-pilot-manifest/0.1',version=VERSION,synthetic_only=True,contains_private_market_data=False,contains_credentials=False,entry='Twstockai_SYNTHETIC_PILOT.html',files=[dict(path=name,bytes=len(raw),sha256=sha(raw)) for name,raw in sorted(files.items())],reused_lite_ui_sha256=ui_sha,dates=sorted(states),stocks_per_date={d:len(s['stocks']) for d,s in states.items()},snapshots=len(snapshots))
    immutable(out/'MANIFEST.json',encoded(manifest))
    archive=out/'Twstockai_ORACLE_PILOT1_SYNTHETIC.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in [*sorted(files),'MANIFEST.json']:
            item=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,(out/name).read_bytes())
    return dict(schema='synthetic-pilot-build/0.1',status='ISOLATED_SYNTHETIC_BUILT_NOT_DEPLOYED',html_bytes=len(files[manifest['entry']]),zip_bytes=archive.stat().st_size,zip_sha256=sha(archive.read_bytes()),elapsed_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,free_bytes=shutil.disk_usage(out).free,manifest=manifest)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(build(a.output),ensure_ascii=False))
