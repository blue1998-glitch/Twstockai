"""Future private-host one-shot entry. Does not register/start any scheduler."""
import argparse,json
from pathlib import Path
from graph_core.market_increment import update
from graph_core_chart.mobile_private import external


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True)
    p.add_argument('--capture',help='Use an already saved receipt; omit for one six-source capture')
    p.add_argument('--correction-of');p.add_argument('--correction-reason');a=p.parse_args()
    root=external(a.root)
    # A missing original filesystem is a block, never a cue to backfill FM3.
    initial=json.loads((root/'fm3-continuation.json').read_bytes())
    if initial['status']!='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS':raise ValueError('Original completed FM3 seed required')
    result=update(root,seed_run=initial['result']['id'],capture_id=a.capture,fetch=not bool(a.capture),
        correction_of=a.correction_of,correction_reason=a.correction_reason)
    if 'terminal_diagnostic' in result:
        result['terminal_diagnostic']={k:v for k,v in result['terminal_diagnostic'].items() if k!='stocks'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('status') in ('BLOCKED','COMMITTED_DURABILITY_UNKNOWN'):raise SystemExit(2)

if __name__=='__main__':main()
