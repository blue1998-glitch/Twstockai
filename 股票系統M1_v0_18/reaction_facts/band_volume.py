"""Bind existing interval-volume helpers to one explicitly selected research source.

No box detection, indicators, representative-volume estimator, UI, I/O or clock.
"""
from copy import deepcopy
from decimal import localcontext

from .core import BINDING, compare, day, timestamp
from .source import make_input
from graph_core.core import fingerprint, number
from pressure_chart.facts import volume_facts
from candle_region_chart.extents import envelope

VERSION = 'explicit-research-band-volume/0.1'
SELECTION = 'explicit-research-band-volume-selection/0.1'


def prepare(data, selection):
    """Reuse the original source/core fingerprint and binding checks, no evaluate."""
    if selection.get('schema_version') != SELECTION:
        raise ValueError('Explicit band-volume selection required')
    if timestamp(selection.get('selected_at')) is None:
        raise ValueError('Actual later selection time required')
    base = make_input(data, dict(schema_version='explicit-reaction-reference-selection/0.1',
                                binding=selection['binding'], selected_at=selection['selected_at'], references=[]))
    context = base['context']
    for k in ('price_mode', 'adjustment_version'):
        if not selection.get(k):
            raise ValueError('Explicit mode/version required')
    if context['price_mode'] != selection['price_mode']:
        raise ValueError('Price mode mismatch')
    version=context.get('adjustment_version', 'NOT_APPLICABLE_RAW' if context['price_mode']=='RAW_CANDIDATE'
                        else 'NOT_RECORDED_IN_SOURCE_SEE_SAVED_PROJECTION')
    if selection['adjustment_version'] != version:
        raise ValueError('Source adjustment-version mismatch')
    if context['volume_unit'] != 'SHARES_REPORTED':
        raise ValueError('Original reported shares required; no implicit unit conversion')
    context['adjustment_version'] = selection['adjustment_version']
    candidates = [b for b in data['core']['boxes'] if b['id'] == selection['candidate_id']]
    if len(candidates) != 1:
        raise ValueError('One explicit existing candidate required')
    box = deepcopy(candidates[0]); members = selection['member_dates']
    if (not members or members != sorted(set(members)) or len(members) != box['duration_records'] or
        members[0] != box['start'] or members[-1] != box['source_end']):
        raise ValueError('Full candidate member dates/count/range required')
    for d in members:
        day(d)
    known = day(box['confirmed_at']); reference_known = day(selection['reference_known_on'])
    if known < members[-1] or reference_known < known:
        raise ValueError('Reference cannot be known before complete candidate confirmation')
    if selection.get('qualification') != 'RESEARCH_CANDIDATE':
        raise ValueError('Research candidate cannot become approved box')
    if box.get('formal_price_bounds') is not None or box.get('formal_region_membership') is not None:
        raise ValueError('This adapter only accepts explicitly qualified research candidates')
    base.update(schema_version='explicit-band-volume-input/0.1', selection=deepcopy(selection), candidate=box)
    return base


def evaluate(payload, *, as_of):
    """Only selected cutoff data; unavailable full source never yields a partial max."""
    day(as_of); c=payload['context']; sel=payload['selection']; box=payload['candidate']
    if payload.get('schema_version') != 'explicit-band-volume-input/0.1':
        raise ValueError('Prepared explicit band input required')
    if fingerprint(payload['bars']) != c['source_prefix_fingerprint']:
        raise ValueError('Input source fingerprint changed')
    if box['id'] != sel['candidate_id']:
        raise ValueError('Selected candidate identity changed')
    if any(sel['binding'].get(k) != c[k] for k in BINDING):
        raise ValueError('Selection binding changed')
    if (sel['price_mode'],sel['adjustment_version']) != (c['price_mode'],c['adjustment_version']):
        raise ValueError('Selection basis/version changed')
    rows=[r for r in payload['bars'] if r['date']<=as_of]
    if not rows or rows[-1]['date'] != as_of or any(a['date']>=b['date'] for a,b in zip(rows,rows[1:])):
        raise ValueError('Exact unique increasing saved analysis prefix required')
    current=rows[-1]
    result=dict(schema_version=VERSION, analysis_as_of=as_of, source_binding={k:deepcopy(c[k]) for k in
                ('code','source_id','price_basis_id','price_mode','adjustment_version','volume_unit')},
                evaluated_prefix_fingerprint=fingerprint(rows),
                selection_origin_binding=deepcopy(sel['binding']),
                origin_binding_role='LATER_SELECTION_ARTIFACT_NOT_HISTORICAL_FRAME',
                selected_at=sel['selected_at'],historical_selection_time=None,
                current_volume_shares=current.get('volume_shares_scaled'), reference=None,
                comparison=compare(None,None,'REFERENCE_NOT_YET_KNOWN'),reasons=[],
                representative_volume_line=dict(status='NOT_IMPLEMENTED',value=None,
                    reason='CLUSTER_MEMBERSHIP_AND_VISUAL_PEAK_ESTIMATOR_UNDEFINED_NO_MEAN_MEDIAN_OR_FIXED_RATIO_SUBSTITUTE'),
                limitations=deepcopy(payload['limits']), historical_signal_eligible=False,
                execution_qualified=False,imputed_close=None,valuation=None,primary_pressure_id=None,
                policy_authorized=False,physical_android='NOT_TESTED_NEW_BUILD')
    # A later chosen candidate does not disclose its complete range/max earlier.
    if as_of < sel['reference_known_on']:
        result['reasons']=['REFERENCE_NOT_YET_KNOWN']
        return _finish(result)
    expected=sel['member_dates']; part=[r for r in rows if box['start']<=r['date']<=box['source_end']]
    dates=[r['date'] for r in part]; missing=[d for d in expected if d not in dates]
    unexpected=[d for d in dates if d not in expected]
    gaps=sorted(d for d in payload.get('known_gap_dates',[]) if box['start']<=d<=box['source_end'])
    resets=sorted(d for d in payload.get('basis_break_dates',[]) if box['start']<=d<=as_of)
    bad=[]
    if missing:bad.append('MISSING_SOURCE_MEMBER_DATES')
    if unexpected:bad.append('UNEXPECTED_SOURCE_MEMBER_DATES')
    if gaps:bad.append('KNOWN_SOURCE_CALENDAR_GAPS')
    if resets:bad.append('BASIS_INTERRUPTION')
    scope_keys=('code','source_id','price_basis_id','price_mode','adjustment_version')
    if any(any(r.get(k,c[k])!=c[k] for k in scope_keys) for r in [*part,current]):
        bad.append('ROW_SOURCE_BASIS_VERSION_CONFLICT')
    missing_volume=[r['date'] for r in part if r.get('volume_shares_scaled') is None]
    if missing_volume:bad.append('MISSING_SOURCE_VOLUME')
    if any(r.get('known_on',r['date'])>as_of or r.get('complete',True) is not True for r in part):
        bad.append('SOURCE_MEMBERS_NOT_YET_KNOWN_OR_INCOMPLETE')
    if fingerprint(part)!=box['display_extent']['source_rows_fingerprint']:
        bad.append('SOURCE_ROWS_FINGERPRINT_CONFLICT')
    ref=dict(candidate_id=box['id'],qualification='RESEARCH_CANDIDATE',formal_price_bounds=None,
             formal_region_membership=None,source_start=box['start'],source_end=box['source_end'],
             expected_records=len(expected),actual_records=len(part),member_dates=deepcopy(expected),
             selected_source_rows_fingerprint=fingerprint(part),candidate_confirmed_on=box['confirmed_at'],
             reference_known_on=sel['reference_known_on'],selected_at=sel['selected_at'],
             max_single_day_shares=None,max_single_day_dates=[],maximum_original_bars=[],source_rows=[],
             missing_member_dates=missing,unexpected_member_dates=unexpected,known_gap_dates=gaps,
             missing_volume_dates=missing_volume,basis_break_dates=resets,
             completeness='UNAVAILABLE',calendar_qualification='EXPLICIT_SAVED_MEMBERS_NOT_CERTIFIED_COMPLETE_MARKET_CALENDAR',
             reused=['graph_core saved candidate.volume','pressure_chart.facts.volume_facts','candle_region_chart.extents.envelope'])
    result['reference']=ref
    if not bad:
        try:
            # Existing maximum/tie logic, not a parallel implementation. The sum
            # returned by volume_facts is unused and is never a representative line.
            values=[number(r['volume_shares_scaled']) for r in part]
            if any(v<0 for v in values):
                raise ValueError('Negative source volume')
            with localcontext() as ctx:
                ctx.prec=max(v.adjusted() for v in values)-min(v.as_tuple().exponent for v in values)+len(str(len(values)))+4
                stats=volume_facts(part)
            extent=envelope(part,0,len(part)-1)
            maximum=stats['max_single_day_shares']; tied=stats['max_single_day_dates']
            saved=box['volume']
            if (saved['records']!=len(part) or saved['known_records']!=len(part) or saved['missing_dates'] or
                compare(maximum,saved['maximum'])['relation']!='EQUAL' or tied!=saved['maximum_dates'] or
                compare(maximum,extent['volume']['max_volume_shares_scaled'])['relation']!='EQUAL' or
                tied!=extent['volume']['known_max_dates']):
                bad.append('EXISTING_VOLUME_HELPERS_OR_SAVED_CANDIDATE_CONFLICT')
            else:
                ref.update(max_single_day_shares=maximum,max_single_day_dates=deepcopy(tied),
                           maximum_original_bars=deepcopy([r for r in part if r['date'] in tied]),
                           source_rows=deepcopy(part),completeness='COMPLETE_EXPLICIT_SAVED_SOURCE_MEMBERS')
        except (ValueError,KeyError,TypeError) as exc:
            bad.append('INVALID_SOURCE_VALUES_OR_OHLC:'+str(exc))
    current_bad=[]
    if current.get('volume_shares_scaled') is None:current_bad.append('MISSING_CURRENT_VOLUME')
    elif number(current['volume_shares_scaled'])<0:current_bad.append('NEGATIVE_CURRENT_VOLUME')
    if current.get('complete',True) is not True or current.get('known_on',as_of)>as_of:
        current_bad.append('CURRENT_RECORD_NOT_YET_KNOWN_OR_INCOMPLETE')
    if any(box['source_end']<d<=as_of for d in payload.get('known_gap_dates',[])):
        current_bad.append('GAP_BETWEEN_REFERENCE_AND_ANALYSIS')
    result['reasons']=bad+current_bad
    result['comparison']=compare(None,None,';'.join(result['reasons'])) if result['reasons'] else compare(
        current['volume_shares_scaled'],ref['max_single_day_shares'],'UNAVAILABLE_FULL_SOURCE_MAXIMUM')
    return _finish(result)


def _finish(result):
    result['available']=result['comparison']['reason']=='AVAILABLE'
    result['result_id']=fingerprint(result)
    return result
