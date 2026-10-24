"""Small case report AFTER diagnosis; manual review never enters the core."""
import argparse
import hashlib
import json
from pathlib import Path
from .build import ROOT,load_html
from product_candidate.build import publish_immutable


def make(html):
    review_path=ROOT.parent/'docs/visual-discussion/20261019_graph_core_review/structural-comparison.json'
    review=json.loads(review_path.read_text());bundle=load_html(html)
    s=next(s for s in bundle['series'] if s['code']==review['code'])
    r=next(r for r in s['results'] if r['as_of']==review['as_of']);d=s['diagnostics'][r['as_of']]
    pivots={p['id']:p for p in r['pivots']};byid={b['id']:b for b in r['boxes']}
    labels={b['label']:b['id'] for b in review['selected_boxes']}
    b=byid[labels['B77']]
    def short(t):
        return dict(id=t['id'],source_start=t['source_start'],source_last_turn=t['source_last_turn'],observed_at=t['observed_at'],
            decision=t['decision'],checks=t['checks'],witness_sources={k:[pivots[i] for i in ids] for k,ids in t['checks']['witnesses'].items()})
    left=[t for t in d['enumeration'] if t['scale']==b['scale'] and t['last_turn_id']==b['source_turn_ids'][-1] and t['first_index']<b['first_index']]
    right=[t for t in d['enumeration'] if t['scale']==b['scale'] and t['first_turn_id']==b['source_turn_ids'][0] and t['last_index']>b['last_index']]
    return dict(schema_version='graph-diagnostic-review/0.1',scope='AFTER_COMPUTATION_CASE_COMPARISON_NOT_CORE_INPUT_OR_NEW_RULE',
        html_sha256=hashlib.sha256(Path(html).read_bytes()).hexdigest(),core_result_id=r['result_id'],diagnostic_id=d['diagnostic_id'],
        source_id=r['context']['source_id'],source_prefix_fingerprint=r['source_prefix_fingerprint'],as_of=r['as_of'],
        original_review=dict(path=str(review_path.relative_to(ROOT.parent)),sha256=hashlib.sha256(review_path.read_bytes()).hexdigest()),
        series=[dict(code=v['code'],latest=v['diagnostics'][v['results'][-1]['as_of']]['summary']) for v in bundle['series']],
        B77=dict(id=b['id'],source_start=b['start'],source_last_turn=b['source_end'],confirmed_at=b['confirmed_at'],
            nearest_earlier_confirmed_start_trial=short(left[-1]) if left else None,
            first_later_confirmed_end_trial=short(right[0]) if right else None,
            earlier_trial_count=len(left),later_trial_count=len(right),
            enumerated_turns_at_same_scale=[p for p in r['pivots'] if p['scale']==b['scale'] and review['month_precision_context']['start_month']<=p['occurred_at'][:7]<=b['start'][:7]],
            explanation='No arbitrary daily/month endpoint starts: only confirmed turns. Nearest earlier turn starts a wider high cluster rejected by the original setting; later low transition fails low cluster. This does not reject the month-only manual major context or establish formal region membership.'),
        selected_case_diagnostics=[dict(label=label,box=byid[labels[label]],diagnostics=next(v for v in d['boxes'] if v['box_id']==labels[label])) for label in ['B44','B80','B77','B88','B89']],
        original_month_context=review['month_precision_context'],original_manual_interval=review['previous_manual_interval'],
        parameters_unchanged=True,original_core_unchanged=True,independent_pattern_count=None,accuracy=None,
        formal_region_membership=None,primary_pressure_id=None,direct_succession='UNKNOWN',
        core_usefulness='NOT_ESTABLISHED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',
        physical_android='NOT_TESTED_NEW_BUILD')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--html',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    report=make(a.html);print(publish_immutable(a.report,json.dumps(report,ensure_ascii=False,indent=2).encode()))
