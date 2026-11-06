"""Measure original full-state shell serialization once, without publishing/calling core."""
import json,resource,time,sys,re,hashlib
from pathlib import Path
from rotation_research import artifact_codec as c
from graph_core.real_workbench import render_saved_shell

def measure(root,out):
 started=time.monotonic();head=json.loads((Path(root)/'current-increment-run.json').read_bytes());raw=c.read_bytes(head['private_preview']['path'])
 state=json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)[1]);parsed=time.monotonic();rebuilt=render_saved_shell(raw,state)
 report=dict(method='Original existing render_saved_shell over complete saved state, output held in memory only; no graph/core/indicator/Journal changes',source_bytes=len(raw),shell_bytes=len(rebuilt),stocks=len(state['stocks']),original_events=sum(len(x['events']) for x in state['radar'].values()),parse_seconds=parsed-started,serialize_seconds=time.monotonic()-parsed,total_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,published_bytes=0)
 Path(out).write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':measure(*sys.argv[1:])
