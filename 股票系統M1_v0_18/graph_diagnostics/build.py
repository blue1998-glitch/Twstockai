"""Add diagnostic sidecars to the exact retained 0.1 numerical bundle."""
import argparse
from copy import deepcopy
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re

from graph_core.core import fingerprint
from graph_core_chart.build import ROOT, selection as original_selection
from technical_chart.build import pack, unpack
from product_candidate.build import publish_immutable
from .diagnose import diagnose

NAME='M1_v019_graph_diagnostics_v01.html'
VIEW_VERSION='graph-diagnostic-view/0.1'
PARENT=ROOT/'graph_core_chart/generated/M1_v019_graph_recognition_v01.html'
PARENT_SHA='fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724'


def load_html(path):
    transport=json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',Path(path).read_text(),re.S).group(1))
    if transport.get('schema_version')=='gzip-interned-chart/0.1':
        transport=json.loads(gzip.decompress(base64.b64decode(transport['data'],validate=True)))
    return unpack(transport)


def input_for(series):
    return dict(schema_version='graph-recognition-input/0.1',context=deepcopy(series['results'][-1]['context']),
        bars=deepcopy(series['bars']),basis_break_dates=deepcopy(series['results'][-1]['data_gaps']['basis_resets']))


def selection(bundle,code,as_of):
    value=original_selection(bundle,code,as_of)
    series=next(s for s in bundle['series'] if s['code']==code)
    value.update(schema_version='graph-diagnostic-selection/0.1',view_version=VIEW_VERSION,
        diagnostics=deepcopy(series['diagnostics'][as_of]))
    return value


def make():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest()!=PARENT_SHA: raise ValueError('Frozen core view changed')
    old=load_html(PARENT)
    if fingerprint({k:v for k,v in old.items() if k!='artifact_id'})!=old['artifact_id']:
        raise ValueError('Parent bundle fingerprint mismatch')
    bundle=deepcopy(old)
    for s in bundle['series']:
        payload=input_for(s);s['diagnostics']={}
        for result in s['results']:
            d=diagnose(payload,result)
            if d['presentation']['selected_ids']!=s['presentations'][result['as_of']]['ids']:
                raise ValueError('Original display selection trace differs')
            s['diagnostics'][result['as_of']]=d
        print(s['code'],len(s['diagnostics']),'diagnostic prefixes',len(d['enumeration']),'latest trials',flush=True)
    bundle.update(schema_version='graph-diagnostic-chart-bundle/0.1',view_version=VIEW_VERSION,
        original_bundle_id=old['artifact_id'],diagnostic_parent_html_sha256=PARENT_SHA)
    del bundle['artifact_id'];bundle['artifact_id']=fingerprint(bundle)
    return bundle


def render_transport(raw):
    here=Path(__file__).parent;old=ROOT/'graph_core_chart'
    template=(old/'template.html').read_text().replace('M1 圖形辨識研究主圖 0.1','M1 圖形辨識追溯診斷 0.1')
    panel='''<details id="diagnosticPanel"><summary>追溯診斷：日期、版本、未選／被拒原因</summary>
<p id="diagnosticSummary"></p><div class="toolbar"><label>診斷候選 <select id="diagBox" aria-label="診斷候選"></select></label><button id="diagEvidence">讀取診斷</button></div>
<div id="diagnosticBody"></div><div class="toolbar"><select id="probeMode" aria-label="診斷串模式"><option value="left">同末轉折的所有起點</option><option value="right">同起點的後來末轉折</option></select><select id="probeSelect" aria-label="診斷轉折串"></select><button id="probeFocus">看此串與原候選</button><button id="probeClear">清除診斷串</button></div>
<div id="probeBody"></div><p>診斷串為原算法實際檢查的轉折串；不代表正式成員或獲認可壓力。只讀已算前綴，不修改原核心、參數或分析日。</p></details>'''
    template=template.replace('<details id="candidates">',panel+'<details id="candidates">')
    style=(old/'viewer.css').read_text()+'\n#diagnosticPanel{overflow-wrap:anywhere}#probeSelect{max-width:100%;width:430px}#diagBox{max-width:100%;width:320px}#diagnosticBody p{margin:7px 0}.diagnostic-facts{color:#ffe1a6}'
    loader='''(async()=>{const el=document.getElementById('payload'),transport=JSON.parse(el.textContent);
if(transport.schema_version!=='gzip-interned-chart/0.1')throw Error('Unknown diagnostic transport');
const bytes=Uint8Array.from(atob(transport.data),c=>c.charCodeAt(0));
el.textContent=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
'''
    api="""\nwindow.M1_DIAGNOSTICS={state:()=>({view:{...view},code:current.code,as_of:result.as_of,result_id:result.result_id,source_id:current.source.id,
core:result,diagnostics:diagnostic(),selection:selected(),geometry:{left:geometry.left,right:geometry.right,price:geometry.price,volume:geometry.volume,macd:geometry.macd},
cursor:bars()[view.cursor],cursor_synchronized:geometry.price.x(view.cursor)===geometry.volume.x(view.cursor)&&geometry.volume.x(view.cursor)===geometry.macd.x(view.cursor),
probe:diagnosticProbe}),boxId:label=>boxes()[Number(label.slice(1))-1]?.id};
})().catch(e=>{document.getElementById('status').textContent='診斷載入失敗：'+e.message;throw e;});"""
    script=loader+(old/'viewer.js').read_text()+'\n'+(here/'viewer.js').read_text()+api
    return template.replace('@@STYLE@@',style).replace('@@DATA@@',raw).replace('@@SCRIPT@@',script)


def render(bundle):
    packed=json.dumps(pack(bundle),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    compressed=gzip.compress(packed,compresslevel=9,mtime=0)
    if gzip.decompress(compressed)!=packed: raise ValueError('Compressed transport mismatch')
    raw=json.dumps(dict(schema_version='gzip-interned-chart/0.1',data=base64.b64encode(compressed).decode()))
    return render_transport(raw)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir)
    if 'output' not in out.parts: raise ValueError('New output leaf required')
    bundle=make()
    files={NAME:render(bundle).encode()}
    oracle=dict(cases=[dict(code=s['code'],as_of=r['as_of'],fingerprint=fingerprint(selection(bundle,s['code'],r['as_of']))) for s in bundle['series'] for r in s['results']])
    files['selection-oracle.json']=json.dumps(oracle,ensure_ascii=False,indent=2).encode()
    for s in bundle['series']:
        files[f"diagnostics-{s['code']}-latest.json"]=json.dumps(s['diagnostics'][s['results'][-1]['as_of']],ensure_ascii=False,separators=(',',':')).encode()
    for name,raw in files.items(): print(name,publish_immutable(out/name,raw),len(raw),hashlib.sha256(raw).hexdigest(),flush=True)


if __name__=='__main__':main()
