"""Display-only 0.2 over immutable 0.1 bytes. Never calls a numeric producer."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'deliveries/m1-p03-structure-state-20261024/artifacts'
NAME = 'M1_P03_structure_state_readable_v02.html'
DATA = ('structure-state.json', 'chart-layer.json', 'facts-input.json', 'scenario.json', 'role-selection.json')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def transform(body, script):
    """Fail closed if a frozen display hook no longer matches; data stays intact."""
    html = body.decode('utf-8')
    replacements = {
        'R=manual?140:110': "R=document.documentElement.dataset.p03Legacy==='on'?(manual?140:110):64",
        'price={top:T,bottom:h*.57},volume={top:h*.62,bottom:h*.76},macd={top:h*.82,bottom:h-B}':
            'price={top:T,bottom:h*.53},volume={top:h*.67,bottom:h*.78},macd={top:h*.85,bottom:h-B}',
        "$('panelZoom').style.top=Math.max(price.top,price.bottom-92)+'px'":
            "$('panelZoom').style.top=(price.bottom+7)+'px'",
    }
    for old, new in replacements.items():
        if html.count(old) != 1:
            raise ValueError('Frozen display geometry hook mismatch: ' + old)
        html = html.replace(old, new, 1)
    hook = '})().catch('
    end = html.rfind(hook)
    if end < 0:
        raise ValueError('Frozen display extension hook missing')
    html = html[:end] + '\n' + script + '\n' + html[end:]
    return html.replace('<title>', '<title>可讀性0.2｜', 1).encode()


def build(out, parent=PARENT):
    parent = Path(parent)
    expected = json.loads((parent/'build-verification.json').read_text())['files']
    bodies = {n:(parent/n).read_bytes() for n in ('M1_P03_structure_state_v01.html', *DATA)}
    for n, b in bodies.items():
        if expected[n] != dict(bytes=len(b), sha256=sha(b)):
            raise ValueError('Frozen parent bytes mismatch: ' + n)
    script = (HERE/'readability.js').read_text()
    new_html = transform(bodies.pop('M1_P03_structure_state_v01.html'), script)
    bodies[NAME] = new_html
    report = dict(schema_version='p03-display-readability/0.2', parent_engine_commit='702e91447ff8c02950efe8edf508658e68aba45d',
                  parent_result_sha256=expected['structure-state.json']['sha256'],
                  numeric_producer_executed=False, numeric_schema_changed=False,
                  preserved_exact_files=list(DATA), display_version='p03-existing-chart/0.2',
                  files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in bodies.items()},
                  physical_android='NOT_TESTED_NEW_BUILD')
    bodies['display-verification.json'] = (json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    out.mkdir(parents=True, exist_ok=True)
    for n,b in bodies.items():
        dest=out/n
        if dest.exists():
            if dest.read_bytes()!=b:
                raise ValueError('Refuse to overwrite differing output: '+str(dest))
        else:
            with dest.open('xb') as f:
                f.write(b)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--parent',type=Path,default=PARENT)
    args=p.parse_args();build(args.output_dir,args.parent)
