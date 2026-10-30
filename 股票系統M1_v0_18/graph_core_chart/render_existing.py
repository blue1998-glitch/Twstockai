"""Render the same fingerprint-verified computed bundle without recalculating it."""
import argparse
import json
from pathlib import Path
import re
from graph_core_chart.build import render,NAME
from graph_core.core import fingerprint
from technical_chart.build import unpack
from product_candidate.build import publish_immutable

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-html',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir)
    if 'output' not in out.parts:raise ValueError('Separate output leaf required')
    source=Path(a.input_html);bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',source.read_text(),re.S).group(1)))
    if fingerprint({k:v for k,v in bundle.items() if k!='artifact_id'})!=bundle['artifact_id']:raise ValueError('Stored result bundle fingerprint mismatch')
    print(NAME,publish_immutable(out/NAME,render(bundle).encode()))
    for name in ['selection-oracle.json','build-verification.json','core-1101-latest.json','core-2884-latest.json','core-6488-latest.json','core-8069-latest.json']:
        print(name,publish_immutable(out/name,(source.parent/name).read_bytes()))
