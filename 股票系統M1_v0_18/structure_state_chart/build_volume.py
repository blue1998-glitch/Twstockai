"""Offline wiring: existing frozen P0-3 results + explicit band maximum facts."""
import argparse,base64,gzip,hashlib,json
from pathlib import Path

from reaction_facts.band_volume import prepare,evaluate

HERE=Path(__file__).parent
APP=HERE.parent
REPO=APP.parent
PARENT=REPO/'deliveries/m1-p03-readability-20261024/artifacts'
NAME='M1_P03_explicit_band_volume_v03.html'
DATA=('structure-state.json','chart-layer.json','facts-input.json','scenario.json','role-selection.json')


def build(out, selection_path, data_path=None, parent=PARENT):
    data_path=Path(data_path or APP/'cross_scale_chart/generated/comparison-data.json')
    data=json.loads(data_path.read_bytes());selection=json.loads(Path(selection_path).read_bytes())
    input_=prepare(data,selection)
    old={n:(Path(parent)/n).read_bytes() for n in DATA}
    frozen=json.loads((Path(parent)/'display-verification.json').read_bytes())['files']
    for n,b in old.items():
        if frozen[n] != dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()):
            raise ValueError('Frozen original JSON differs: '+n)
    # The old five JSONs are copied without running any state/indicator producer.
    p03=json.loads(old['chart-layer.json'])
    if (p03['original_comparison_artifact_id']!=data['artifact_id'] or
        p03['source_data_file_sha256']!=hashlib.sha256(data_path.read_bytes()).hexdigest()):
        raise ValueError('Explicit volume source differs from frozen P0-3 source')
    snapshots={r['date']:evaluate(input_,as_of=r['date']) for r in data['bars'] if r['date']<=data['as_of']}
    output=dict(schema_version='explicit-band-volume-chart-layer/0.1',selection=selection,
                series_key=p03['series_key'],frame_map=p03['frame_map'],snapshots=snapshots,
                original_comparison_artifact_id=data['artifact_id'],original_p03_result_id=p03['result']['result_id'],
                indicator_or_graph_or_p03_recalculated=False,physical_android='NOT_TESTED_NEW_BUILD')
    from graph_core.core import fingerprint
    output['artifact_id']=fingerprint(output)
    body=json.dumps(output,ensure_ascii=False,separators=(',',':')).encode()
    encoded=base64.b64encode(gzip.compress(body,mtime=0)).decode()
    patch="\nconst bandVolumeCompressed=Uint8Array.from(atob('"+encoded+"'),x=>x.charCodeAt(0));\n"
    patch+="const bandVolumeData=JSON.parse(await new Response(new Blob([bandVolumeCompressed]).stream().pipeThrough(new DecompressionStream('gzip'))).text());\n"
    patch+=(HERE/'band_volume.js').read_text()
    html=(Path(parent)/'M1_P03_structure_state_readable_v02.html').read_text()
    if frozen['M1_P03_structure_state_readable_v02.html'] != dict(bytes=len(html.encode()),sha256=hashlib.sha256(html.encode()).hexdigest()):
        raise ValueError('Frozen original HTML differs')
    needle='drawRegionVolumeBands(ctx,x,volume,maxVol,step);'
    if html.count(needle)!=1:raise ValueError('Frozen volume scale hook differs')
    html=html.replace(needle,'geometry.volume.displayMaximum=maxVol;'+needle,1)
    at=html.rfind('})().catch(')
    if at<0:raise ValueError('Frozen chart extension hook missing')
    html=html[:at]+patch+'\n'+html[at:]
    html=html.replace('<title>','<title>明示研究段最大量｜',1)
    files={**old,NAME:html.encode(),'band-volume.json':body,'band-volume-selection.json':Path(selection_path).read_bytes()}
    report=dict(status='PASS',schema_version='explicit-band-volume-build/0.1',
                reused_maximum_helpers=True,graph_p03_indicators_or_routing_recomputed=False,
                frozen_five_json_exact=True,current=snapshots[data['as_of']],
                files={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()})
    files['volume-build-verification.json']=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    out.mkdir(parents=True,exist_ok=True)
    for n,b in files.items():
        p=out/n
        if p.exists():
            if p.read_bytes()!=b:raise ValueError('Preserve different existing output '+str(p))
        else:
            with p.open('xb') as f:f.write(b)
    print(json.dumps({k:v for k,v in report.items() if k!='current'},ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True);p.add_argument('--data',type=Path)
    a=p.parse_args();build(a.output_dir,a.selection,a.data)
