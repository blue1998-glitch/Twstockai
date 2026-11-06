"""Bind a display-only rerender to actual prior numerical re-execution evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from .build import render_transport
from product_candidate.build import publish_immutable


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--previous-dir',required=True);p.add_argument('--final-dir',required=True);a=p.parse_args()
    previous=Path(a.previous_dir);final=Path(a.final_dir);name='M1_v019_graph_diagnostics_v01.html'
    before=(previous/name).read_bytes();after=(final/name).read_bytes();evidence=json.loads((previous/'artifact-verification.json').read_text())
    if evidence['status']!='PASS' or hashlib.sha256(before).hexdigest()!=evidence['html_sha256']:raise ValueError('Prior actual numeric test identity mismatch')
    def transport(raw):return re.search(r'id="payload"[^>]*>(.*?)</script>',raw.decode(),re.S).group(1)
    if transport(before)!=transport(after):raise ValueError('Numeric transport not byte-identical')
    if render_transport(transport(after)).encode()!=after:raise ValueError('Final HTML differs from current display source')
    names=['selection-oracle.json',*[f.name for f in previous.glob('diagnostics-*-latest.json')]]
    for n in names:
        if (previous/n).read_bytes()!=(final/n).read_bytes():raise ValueError('Numeric sidecar changed')
    report=dict(status='PASS',html_sha256=hashlib.sha256(after).hexdigest(),
        previous_numerically_recomputed_html_sha256=evidence['html_sha256'],
        numeric_transport_byte_identical=True,current_display_source_reproduces_html=True,
        prior_core_prefixes_recomputed=evidence['core_prefixes_recomputed'],prior_diagnostic_prefixes_recomputed=evidence['diagnostic_prefixes_recomputed'],
        prior_numeric_report_sha256=hashlib.sha256((previous/'artifact-verification.json').read_bytes()).hexdigest(),
        numeric_prefixes_recomputed_this_command=0,oracles_unchanged=evidence['oracles'],series=evidence['series'],
        scope='Verified actual prior full re-execution and byte-identical numeric transport, not a second numerical rerun',
        android='NOT_TESTED_NEW_BUILD',core_usefulness='NOT_ESTABLISHED')
    print(publish_immutable(final/'artifact-verification-final.json',json.dumps(report,ensure_ascii=False,indent=2).encode()))
