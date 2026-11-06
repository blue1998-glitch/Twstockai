"""Re-render existing byte-identical numeric transport without recomputation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from .build import NAME,render_transport,load_html
from graph_core.core import fingerprint
from product_candidate.build import publish_immutable


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args()
    src=Path(a.input_dir);out=Path(a.output_dir)
    if 'output' not in out.parts:raise ValueError('New output leaf required')
    original=(src/NAME).read_bytes();bundle=load_html(src/NAME)
    if fingerprint({k:v for k,v in bundle.items() if k!='artifact_id'})!=bundle['artifact_id']:raise ValueError('Invalid original numeric bundle')
    transport=re.search(r'id="payload"[^>]*>(.*?)</script>',original.decode(),re.S).group(1)
    rendered=render_transport(transport).encode()
    if re.search(r'id="payload"[^>]*>(.*?)</script>',rendered.decode(),re.S).group(1)!=transport:raise ValueError('Transport changed')
    files={NAME:rendered,'selection-oracle.json':(src/'selection-oracle.json').read_bytes()}
    files.update({f.name:f.read_bytes() for f in src.glob('diagnostics-*-latest.json')})
    files['render-verification.json']=json.dumps(dict(status='PASS',numeric_transport_byte_equal=True,
        original_html_sha256=hashlib.sha256(original).hexdigest(),html_sha256=hashlib.sha256(rendered).hexdigest(),
        artifact_id=bundle['artifact_id'],note='Clarify research range boundary wording, no numeric recomputation'),indent=2).encode()
    for k,v in files.items():print(k,publish_immutable(out/k,v),len(v),hashlib.sha256(v).hexdigest())
