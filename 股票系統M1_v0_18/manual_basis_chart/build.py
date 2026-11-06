"""Reuse a fixed chart without recomputing old indicators or recognition."""
import argparse,base64,gzip,hashlib,json,re,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from manual_basis.core import fingerprint,validate_catalogue,resolve
from technical_chart.build import unpack
from candle_region_chart.build import selection as saved_selection

PARENT=ROOT.parent/'deliveries/m1-v019-soft-regions-v043-20261019/M1_v019_soft_regions_v043.zip'
PARENT_SHA='ee5362de516d52f43b2d09f76b46c04345fd147a2beced4a32e208fbfaf41212'
NAME='M1_v019_manual_basis_v01.html'

def load_parent():
    body=PARENT.read_bytes()
    if hashlib.sha256(body).hexdigest()!=PARENT_SHA:raise ValueError('Frozen parent ZIP mismatch')
    with zipfile.ZipFile(PARENT) as archive:
        if archive.testzip() is not None:raise ValueError('Parent ZIP CRC mismatch')
        html=archive.read('M1_v0_19_soft_regions_v043.html').decode()
    match=re.search(r'<script type="application/json" id="payload">(.*?)</script>',html,re.S)
    payload=unpack(json.loads(match.group(1)))
    return html,match,payload

def catalogue_from(payload):
    entries=[]
    for series in [*payload['numbers']['series'],*payload['history_series']]:
        for frame in series['frames']:
            n=frame['index']+1;base=series['bases'][frame['chart_base']]
            if frame['code']!=series['code'] or frame['price_mode']!=series['price_mode']:raise ValueError('Mode/code mismatch')
            if base['bars'][n-1]['date']!=frame['as_of'] or len(base['macd'])<n or any(len(v)<n for v in base['moving_averages'].values()):raise ValueError('Inconsistent stored price/indicator prefix')
            evidence=payload['evidence'][series['key']][frame['index']]
            if evidence['as_of']!=frame['as_of']:raise ValueError('Evidence date mismatch')
            entries.append(dict(series_key=series['key'],code=series['code'],price_mode=series['price_mode'],as_of=frame['as_of'],source_id=series['source']['id'],price_basis_id=frame['chart_base'],frame_id=frame['frame_id'],adjustment_version='NOT_APPLICABLE_RAW' if series['price_mode']=='RAW_CANDIDATE' else 'NOT_RECORDED_IN_SOURCE_SEE_SAVED_PROJECTION',coverage=series['coverage'],kind=series.get('kind','ORIGINAL_SAVED_RESEARCH'),bars=n))
    value=dict(schema_version='manual-basis-catalogue/0.1',parent_artifact_id=payload['artifact_id'],entries=entries,scope='SAVED_RESEARCH_ONLY_NOT_FULLY_AUTHENTICATED_ADJUSTED_HISTORY')
    value['catalogue_id']=fingerprint(value);return validate_catalogue(value)

def render(html,match,catalogue):
    # Preserve the original interned numeric tree byte-for-byte before compression.
    compressed=base64.b64encode(gzip.compress(match.group(1).encode(),mtime=0)).decode()
    html=html[:match.start(1)]+compressed+html[match.end(1):]
    old="const data=decode(JSON.parse($('payload').textContent));$('payload').remove();"
    new="const compressed=Uint8Array.from(atob($('payload').textContent),x=>x.charCodeAt(0));const decoded=await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).text();const data=decode(JSON.parse(decoded));$('payload').remove();"
    if html.count(old)!=1:raise ValueError('Unexpected parent decoder')
    html=html.replace(old,new).replace('基底 <select id="mode" aria-label="價格基底"','資料來源 <select id="mode" aria-label="資料來源"')
    html=html.replace('<script>','<script>(async()=>{',1)
    patch=(Path(__file__).parent/'manual_patch.js').read_text()
    # Catalogue is independent routing metadata, not altered numeric evidence.
    encoded=json.dumps(catalogue,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    patch='\nconst manualCatalogue='+encoded+';\n'+patch
    end=html.rfind('</script>')
    html=html[:end]+patch+"\n})().catch(e=>{document.body.replaceChildren();const p=document.createElement('p');p.textContent='載入失敗，未顯示分析：'+e.message;document.body.append(p);});"+html[end:]
    html=html.replace('<title>','<title>人工分析模式 0.1｜',1)
    return html.encode()

def build(out):
    html,match,payload=load_parent();catalogue=catalogue_from(payload)
    out.mkdir(parents=True,exist_ok=True)
    files={NAME:render(html,match,catalogue),'catalogue.json':json.dumps(catalogue,ensure_ascii=False,separators=(',',':')).encode()}
    samples=[]
    for code,mode,day in [('1101','RAW_CANDIDATE','2026-10-16'),('8069','ADJUSTED_CANDIDATE','2026-09-30'),('6488','ADJUSTED_CANDIDATE','2026-07-16'),('2884','ADJUSTED_CANDIDATE','2026-09-30')]:
        choices=[r for r in catalogue['entries'] if r['code']==code and r['price_mode']==mode and r['as_of']==day]
        # These explicit fixture source selectors do not silently become UI defaults.
        if len(choices)>1:choices=[r for r in choices if r['kind']=='NEW_OFFICIAL_RAW_HISTORY']
        key=choices[0]['series_key'] if choices else None
        q=dict(schema_version='manual-basis-request/0.1',selection_id=f'oracle-{code}-{mode}',selected_at='2026-10-22T08:00:00+08:00',code=code,price_mode=mode,as_of=day,series_key=key)
        result=resolve(catalogue,q)
        samples.append(dict(request=q,resolution=result,saved_selection=saved_selection(payload,key,day) if choices else None))
    files['selection-oracle.json']=json.dumps(samples,ensure_ascii=False,separators=(',',':')).encode()
    for name,body in files.items():
        dest=out/name
        if dest.exists() and dest.read_bytes()!=body:raise ValueError('Refuse overwrite changed output '+str(dest))
        dest.write_bytes(body)
    report=dict(parent_zip_sha256=PARENT_SHA,parent_artifact_id=payload['artifact_id'],catalogue_id=catalogue['catalogue_id'],frames=len(catalogue['entries']),new_numeric_calculations=0,original_interned_payload_preserved=True,files={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()},android='NOT_TESTED_NEW_BUILD')
    (out/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);build(p.parse_args().output_dir)
