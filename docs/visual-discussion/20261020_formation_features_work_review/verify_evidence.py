"""Independent arithmetic and source checks for research outputs, not classifier tests."""
from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
import argparse,hashlib,json
from pypdf import PdfReader

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);raw=Path(a.source).read_bytes();s=json.loads(raw)
e=json.loads((p/'evidence.json').read_text());v=json.loads((p/'verification.json').read_text())
assert hashlib.sha256(raw).hexdigest()==e['source_sha256']
checks=0
for case,profile in [('reviewed_case',e['suffix_profiles']['reviewed_case']),('selected_control',e['suffix_profiles']['selected_control'])]:
    original=e[case]['bars']
    for m in [e[case]['metrics']]+profile:
        rows=[r for r in original if m['start']<=r['date']<=m['end']]
        assert len(rows)==m['records'] and all(r in s['bars'] for r in rows)
        assert all(r['date']<=m['end']<=e['data_cutoff'] for r in rows)
        events=defaultdict(int)
        for b in rows:
            events[D(b['low'])]+=1;events[D(b['high'])]-=1
        # Sweep positive-width cells. Coincident endpoints handled by one event.
        active=0;peak=0
        levels=sorted(events)
        for price in levels[:-1]:
            active+=events[price];peak=max(peak,active)
        assert peak==m['peak_range_coverage']
        cs=[D(b['close'])for b in rows]
        ups=sum((max(b-a,0)for a,b in zip(cs,cs[1:])),D(0))
        downs=sum((max(a-b,0)for a,b in zip(cs,cs[1:])),D(0))
        assert ups-downs==D(m['net_close_change'])
        assert ups+downs==D(m['gross_close_path'])
        if ups+downs:assert abs(ups-downs)/(ups+downs)==D(m['directional_efficiency'])
        else:assert m['directional_efficiency']is None
        low=min(D(b['low'])for b in rows);high=max(D(b['high'])for b in rows)
        dates=[b['date']for b in rows if D(b['low'])==low]
        last_low=dates[-1]
        assert last_low==m['latest_window_min_low_date']
        assert sum(b['date']>last_low for b in rows)==m['records_since_latest_window_min_low']
        if high>low:assert (cs[-1]-low)/(high-low)==D(m['last_close_position_in_observed_range'])
        checks+=1
assert checks==24
scan=json.loads((p/'control-scan.json').read_text())
rs=scan['ranked_candidates']
assert len(rs)==128
assert rs==sorted(rs,key=lambda m:(-D(m['directional_efficiency']),m['start']))
assert rs[0]==e['selected_control']['metrics']
assert all(z['human_interval_label']is None for z in [e['selected_control']])
reader=PdfReader(p/'output/pdf/m1-formation-evidence-comparison.pdf')
assert len(reader.pages)==3
assert all(float(page.mediabox.width)==1224 and float(page.mediabox.height)==864 for page in reader.pages)
v['independent_arithmetic_crosscheck']={'method':'Sweep-line range coverage; separate up/down-close sums; extreme-date and location checks against original bars.','profile_records_checked':checks,'result':'PASS'}
v['ranked_control_and_original_source_membership']='PASS'
abc=e['boundary_case'];assert len(abc['bars'])==39 and abc['metrics']['records_since_latest_window_min_low']==0
comp_raw=Path(a.comparison).read_bytes();comp=json.loads(comp_raw)
assert hashlib.sha256(comp_raw).hexdigest()==abc['source_comparison_sha256']
assert abc['bars']==[b for b in comp['bars']if '2025-04-07'<=b['date']<='2025-06-02']
assert min(D(b['low'])for b in abc['bars'])==D(abc['bars'][-1]['low'])==D('27.65')
assert abc['bars'][-1]['date']=='2025-06-02' and abc['bars'][-1]['close']=='27.70'
v['PDF_structure']={'pages':3,'page_points':[1224,864],'result':'PASS'}
qa=json.loads((p/'manual-qa.json').read_text())
assert hashlib.sha256((p/'output/pdf/m1-formation-evidence-comparison.pdf').read_bytes()).hexdigest()==qa['PDF_sha256']
assert len(qa['pages'])==3
for page in qa['pages']:
    assert hashlib.sha256((p/page['path']).read_bytes()).hexdigest()==page['sha256']
v['PDF_render_visual_QA']='PASS_SAVED_MANUAL_QA_RECORD_HASHES_MATCH_CURRENT_PDF_AND_PREVIEWS_NOT_AN_AUTOMATIC_VISUAL_TEST'
v['preview_first_page_label_collision']='FIXED_WITH_EXPLICIT_GROUP_SPACER'
v['PDF_write_failure']='POPPLER_INVALID_XREF_OBSERVED; reproduced after sequential execution, so concurrency root cause NOT_ESTABLISHED. Final PDF completed in BytesIO then written once; byte equality, pypdf and Poppler verified.'
v['run_count_note']='7 research.py invocations: first layout, label/layout revision, added extreme/location features, sequential rebuild, added ABC39 boundary case, in-memory PDF completion and single write, final multi-year date labels. Original core/indicator computations never invoked.'
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'independent_profiles':checks,'PDF_pages':3,'result':'PASS'}))
