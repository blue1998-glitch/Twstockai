"""Read shipped results only. No import/execution/tuning of recognition core."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ZIP_SHA='934c54ec033de14d402cb4b8110ed53e9a99b311a934144f9139950c05046783'
HTML_SHA='fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724'
CORE_SHA='f13275f3ba1e932db4aca5cbc588b61a3d7c5ed48db34797290e63ed6a7f10ec'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(archive):
    assert sha(archive.read_bytes())==ZIP_SHA
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==9
        html=z.read('M1_v019_graph_recognition_v01.html')
        core=z.read('core-1101-latest.json')
        assert sha(html)==HTML_SHA and sha(core)==CORE_SHA
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            h,n=line.split(None,1);assert sha(z.read(n.strip().lstrip('*')))==h
    r=json.loads(core);p=json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>',html.decode(),re.S)[1]);memo={}
    def decode(i):
        if i in memo:return memo[i]
        n=p['nodes'][i];v=n[1] if n[0]=='s' else [decode(x) for x in n[1:]] if n[0]=='a' else {k:decode(x) for k,x in n[1:]};memo[i]=v;return v
    data=decode(p['root']);s=next(x for x in data['series'] if x['code']=='1101')
    assert s['results'][-1]==r
    boxes=r['boxes'];pivots={p['id']:p for p in r['pivots']};labels={b['id']:'B'+str(i+1) for i,b in enumerate(boxes)}
    def compact(n):
        b=boxes[n-1]
        return dict(label='B'+str(n),id=b['id'],scale=b['scale'],source_start=b['start'],source_end=b['source_end'],confirmed_at=b['confirmed_at'],records=b['duration_records'],turns=b['turns'],research_bounds=b['research_bounds'],formal_price_bounds=b['formal_price_bounds'],formal_region_membership=b['formal_region_membership'],first_departure_range_end=b['path']['first_departure_range_end'],first_breakdown_at=b['path']['first_breakdown_at'],parent_ids=b['parent_ids'],successor_count=len(b['successor_after_breakdown_ids']),source_turns=[dict(date=pivots[x]['occurred_at'],kind=pivots[x]['kind'],price=pivots[x]['price'],confirmed_at=pivots[x]['confirmed_at']) for x in b['source_turn_ids']])
    month_rows=[b for b in s['bars'] if '2023-06'<=b['date'][:7]<='2025-04'];long=boxes[76]
    manual=[b for b in s['bars'] if '2025-04-07'<=b['date']<='2025-06-02']
    assert len(month_rows)==463 and len(manual)==39
    assert not [b for b in boxes if b['start']=='2025-04-07' and b['source_end']=='2025-06-02']
    def geometry(n):return [(pivots[i]['occurred_at'],pivots[i]['kind'],pivots[i]['price']) for i in boxes[n-1]['source_turn_ids']]
    assert geometry(44)==geometry(80)
    chain=[67,68,70,72,74,76,77]
    assert all(boxes[b-1]['source_turn_ids'][:len(boxes[a-1]['source_turn_ids'])]==boxes[a-1]['source_turn_ids'] for a,b in zip(chain,chain[1:]))
    return dict(schema_version='work-graph-structure-comparison/0.1',scope='READ_ONLY_SHIPPED_RESULT_NOT_ENGINE_RERUN',artifact_commit='2d480bffcaebfa09768e04a283227effc3fc0a00',zip_sha256=ZIP_SHA,html_sha256=HTML_SHA,core_sha256=CORE_SHA,as_of=r['as_of'],source_id=r['context']['source_id'],price_basis_id=r['context']['price_basis_id'],numeric_frame_id=s['numeric_frame_ids'][r['as_of']],source_prefix_fingerprint=r['source_prefix_fingerprint'],core_result_id=r['result_id'],code='1101',close=r['anchor']['close'],source_records=r['source_records'],selected_boxes=[compact(n)for n in [22,24,44,66,67,68,70,72,74,76,77,80,83,88,89]],month_precision_context=dict(start_month='2023-06',end_month='2025-04',formal_start=None,formal_end=None,display_month_rows=463,B77_source_rows=333,display_rows_before_B77=97,display_rows_after_B77=33,qualification='DISPLAY_CONTEXT_COUNTS_NOT_APPROVED_MEMBERSHIP_OR_RECALL'),previous_manual_interval=dict(start='2025-04-07',end='2025-06-02',records=39,exact_auto_source_interval_matches=[],qualification='USER_REPORTED_SOURCE_VERIFIED_TIME_RANGE_NOT_CORE_INPUT'),same_geometry_cross_scale=dict(labels=['B44','B80'],same_source_turn_date_kind_price=True,confirmations=['2025-05-14','2025-05-27'],independent_pattern_votes=False),same_scale_source_turn_prefix_chain=dict(labels=['B'+str(n)for n in chain],qualification='EXACT_PREFIX_LINEAGE_OBSERVED_NOT_USER_APPROVED_MERGE'),default_presented=[labels[i]for i in s['presentations'][r['as_of']]['ids']],jan27_pivots=[p for p in r['pivots']if p['kind']=='HIGH' and p['occurred_at']=='2026-01-27' and p['price']=='26.95'],B88_latest_events=[dict(date=e['date'],type=e['type'],close=e['close']) for e in boxes[87]['path']['events'] if e['date']>='2026-10-12'],validation=dict(package_crc_and_fingerprints='PASS',embedded_latest_equals_separate_core=True,manual_date_counts='PASS',cross_scale_geometry='PASS',same_scale_prefix_chain='PASS',core_executed=False,parameters_changed=False,android='NOT_TESTED_NEW_BUILD',quality='NOT_VALIDATED',core_usefulness='NOT_ESTABLISHED',action='NOT_EVALUATED'))
if __name__=='__main__':
    archive=Path(sys.argv[1]);out=Path(sys.argv[2]);out.write_text(json.dumps(read(archive),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('READ_ONLY_COMPARISON_VERIFIED')
