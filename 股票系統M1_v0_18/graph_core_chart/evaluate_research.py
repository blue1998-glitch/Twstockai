"""Describe shipped results and parameter sensitivity; never call this accuracy."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import re
from graph_core_chart.build import input_for
from graph_core.core import analyze,DEFAULT_CONFIG
from candle_region_chart.build import load_parent
from technical_chart.build import unpack
from product_candidate.build import publish_immutable


def evaluate(html):
    raw=Path(html).read_bytes();bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',raw.decode(),re.S).group(1)));parent=load_parent();records=[]
    for s in bundle['series']:
        r=s['results'][-1];old=next(v for v in parent['history_series'] if v['code']==s['code']);payload=input_for(old,old['frames'][-1]);sensitivity=[]
        configs=[dict(reversals=['0.025','0.05','0.10']),dict(cluster_spread_fraction='0.25')]
        for change in configs:
            cfg=deepcopy(DEFAULT_CONFIG);cfg.update(change);other=analyze(payload,as_of=r['as_of'],config=cfg)
            sensitivity.append(dict(parameters=cfg,boxes=len(other['boxes']),pivots=len(other['pivots']),frontier=len(other['comparison']['pareto_frontier_ids']),result_id=other['result_id'],qualification='EXPLORATORY_SENSITIVITY_NOT_OPTIMIZED_TO_MANUAL_CASES'))
        audit=s['manual_audits'].get(r['as_of']);records.append(dict(code=s['code'],as_of=r['as_of'],close=r['anchor']['close'],source_rows=r['source_records'],
            pivots=len(r['pivots']),boxes=len(r['boxes']),parent_child_relations=sum(len(b['parent_ids']) for b in r['boxes']),
            relevant_upper_pressure=len(r['comparison']['relevant_pressure_ids']),research_frontier=len(r['comparison']['pareto_frontier_ids']),
            primary_pressure_id=None,anchor_volume=r['anchor_volume'],
            presented=[{k:b[k] for k in ['id','scale','start','source_end','confirmed_at','research_bounds','duration_records','turns','anchor_relation']} for b in r['boxes'] if b['id'] in s['presentations'][r['as_of']]['ids']],
            manual_case_audit=audit,parameter_sensitivity=sensitivity))
    return dict(schema_version='graph-recognition-evidence-audit/0.1',source_html_sha256=hashlib.sha256(raw).hexdigest(),series=records,
        execution_scope='AUTOMATIC_ENGINE_AND_PREFIX_ENGINEERING_VALIDATION',recognition_accuracy='NOT_MEASURED_NO_ADJUDICATED_MARKET_TEST_SET',
        manual_exact_interval_mismatch='1101 user39-record box has no exact automatic interval match; do not tune to or overwrite the case',
        larger_pressure_limit='Longest displayed automatic context is not the fully reproduced month-only user major band; formal importance remains unresolved',
        image_model_training='NOT_EXECUTED_OR_CLAIMED',core_usefulness='NOT_ESTABLISHED',physical_android='NOT_TESTED_NEW_BUILD')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--html',required=True);p.add_argument('--report',required=True);a=p.parse_args();r=evaluate(a.html)
    print(publish_immutable(a.report,json.dumps(r,ensure_ascii=False,indent=2).encode()));print('PASS descriptive audit; accuracy NOT_MEASURED')
