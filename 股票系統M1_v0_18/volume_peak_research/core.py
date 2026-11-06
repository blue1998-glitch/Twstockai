"""Pure explicit-config peak/span hypotheses. No I/O, clock, UI or signals."""
from copy import deepcopy
from decimal import localcontext

from graph_core.core import fingerprint, number
from reaction_facts.core import BINDING, compare, day, timestamp
from pressure_chart.facts import volume_facts
from contracts import validate_candles

VERSION = 'explicit-volume-peak-research/0.1'
INPUT = 'explicit-volume-peak-research-input/0.1'
CONFIG_STATUS = 'RESEARCH_PROBE_NOT_APPROVED_NO_DEFAULT_OR_OPTIMUM'
SCOPE = (*BINDING[:3], 'price_mode', 'adjustment_version', 'volume_unit')


def _within(low, high, ratio):
    # Exact product; never divide/round a boundary ratio or use binary floats.
    with localcontext() as ctx:
        ctx.prec = len(low.as_tuple().digits) + len(ratio.as_tuple().digits) + 4
        return high <= low * ratio


def _finish(result):
    result['result_id'] = fingerprint(result)
    return result


def _peaks(rows, k, reference_known_on):
    """Non-platform rule only. Equal neighboring top dates remain unresolved."""
    values = [number(r['volume_shares_scaled']) for r in rows]
    assessments, confirmed, ambiguous = [], [], set()
    for i, value in enumerate(values):
        left = values[max(0, i-k):i]
        right = values[i+1:i+k+1]
        neighbors = list(range(max(0, i-k), i)) + list(range(i+1, min(len(rows), i+k+1)))
        equals = [j for j in neighbors if values[j] == value]
        # A tied potential top must not become the first day via >left/>=right.
        # No platform boundary/representative rule was approved: retain all tied
        # dates and refuse complete grouping, including noncontiguous nearby ties.
        if equals and all(values[j] <= value for j in neighbors):
            ambiguous.update([i, *equals])
            status = 'AMBIGUOUS_EQUAL_VOLUME_NEIGHBORHOOD'
        elif len(left) < k:
            status = 'INSUFFICIENT_LEFT_RECORDS'
        elif value <= max(left) or (right and value < max(right)):
            status = 'NOT_NON_PLATFORM_PEAK'
        elif len(right) < k:
            status = 'PENDING_RIGHT_RECORDS'
        else:
            status = 'CONFIRMED_NON_PLATFORM_PEAK'
        assessment = dict(date=rows[i]['date'], status=status,
                          left_records=len(left), right_records=len(right), required_each_side=k,
                          confirmed_on=None, original_bar=deepcopy(rows[i]))
        if status == 'CONFIRMED_NON_PLATFORM_PEAK':
            window = rows[i-k:i+k+1]
            confirmed_on = max(r.get('known_on', r['date']) for r in window)
            known = max(reference_known_on, confirmed_on,
                        *(r.get('known_on', r['date']) for r in window))
            assessment.update(confirmed_on=confirmed_on, known_on=known,
                              right_window_end_on=rows[i+k]['date'],
                              comparison_window_dates=[r['date'] for r in window])
            confirmed.append(deepcopy(assessment))
        assessments.append(assessment)
    return assessments, confirmed, [deepcopy(rows[i]) for i in sorted(ambiguous)]


def _groups(peaks, ratio, config, reference, current, comparison_reason):
    ordered = sorted(peaks, key=lambda p: (number(p['original_bar']['volume_shares_scaled']), p['date']))
    values = [number(p['original_bar']['volume_shares_scaled']) for p in ordered]
    result = []
    for lo in range(len(ordered)):
        if lo and values[lo] == values[lo-1]:
            continue  # A maximal group must include ALL equal-valued originals.
        hi = lo
        while hi+1 < len(ordered) and _within(values[lo], values[hi+1], ratio):
            hi += 1
        if lo and _within(values[lo-1], values[hi], ratio):
            continue  # Extendable to the left; not inclusion-maximal.
        members = sorted(ordered[lo:hi+1], key=lambda p: p['date'])
        low = ordered[lo]['original_bar']['volume_shares_scaled']
        high = ordered[hi]['original_bar']['volume_shares_scaled']
        group = dict(member_dates=[p['date'] for p in members],
                     original_bars=[deepcopy(p['original_bar']) for p in members],
                     vote_count=len(members), independent_reaction_count=None,
                     min_volume_shares=low, max_volume_shares=high,
                     min_dates=[p['date'] for p in members if number(p['original_bar']['volume_shares_scaled']) == values[lo]],
                     max_dates=[p['date'] for p in members if number(p['original_bar']['volume_shares_scaled']) == values[hi]],
                     maximality=dict(full_span_rule='max <= min * r; exact decimal product',
                         next_lower_peak=None if lo == 0 else deepcopy(ordered[lo-1]['original_bar']),
                         next_upper_peak=None if hi+1 == len(ordered) else deepcopy(ordered[hi+1]['original_bar']),
                         left_extension_fails_or_source_edge=True, right_extension_fails_or_source_edge=True),
                     confirmed_on=max(p['confirmed_on'] for p in members),
                     known_on=max(p['known_on'] for p in members),
                     evaluation_as_of=reference['evaluation_as_of'],
                     source_assessment_end=reference['source_end'],
                     source_member_fingerprint=reference['member_fingerprint'],
                     config=deepcopy(config), candidate_anchor=None,
                     qualification='UNVALIDATED_ENGINE_HYPOTHESIS',
                     ambiguities=['OVERLAPPING_GROUPS_ARE_ALTERNATIVES_NOT_INDEPENDENT_REACTIONS',
                                  'NO_UNIQUE_REPRESENTATIVE_LINE_OR_IMPORTANCE_SELECTION'],
                     comparisons={name: compare(current, endpoint, comparison_reason) for name, endpoint in
                                  [('to_min', low), ('to_max', high),
                                   ('to_original_maximum', reference['maximum']['max_single_day_shares'])]})
        group['id'] = fingerprint(dict(member_dates=group['member_dates'], config=config,
                                      source_member_fingerprint=reference['member_fingerprint']))
        result.append(group)
    return result


def evaluate(payload, *, config):
    """Evaluate only payload.as_of prefix. Invalid declarations raise, evidence gaps refuse.

    Binding fingerprint refers to this cutoff prefix, never the full future input.
    Config is mandatory; there are no k/r defaults or optimizer.
    """
    if payload.get('schema_version') != INPUT:
        raise ValueError('Explicit research input required')
    if set(config) != {'k', 'r', 'qualification'} or config['qualification'] != CONFIG_STATUS:
        raise ValueError('Explicit unapproved research config required')
    k = config['k']
    if type(k) is not int or k < 1:
        raise ValueError('Positive integer k required')
    ratio = number(config['r'])
    if ratio < 1:
        raise ValueError('Full-span ratio r must be at least one')
    as_of = day(payload['as_of']); context = payload['context']; selection = payload['selection']
    if any(not isinstance(context.get(key), str) or not context[key] for key in SCOPE + BINDING):
        raise ValueError('Complete explicit source/basis/version binding required')
    if context['volume_unit'] != 'SHARES_REPORTED':
        raise ValueError('SHARES_REPORTED required; no conversion')
    if context['price_mode'] not in ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE'):
        raise ValueError('Explicit price mode required')
    if selection.get('binding') != {key: context[key] for key in BINDING}:
        raise ValueError('Selection binding conflict')
    if any(selection.get(key) != context[key] for key in SCOPE):
        raise ValueError('Selection source/basis/version/unit conflict')
    if selection.get('qualification') != 'RESEARCH_CANDIDATE' or not selection.get('candidate_id'):
        raise ValueError('Explicit research candidate required')
    if selection.get('formal_price_bounds') is not None or selection.get('formal_region_membership') is not None:
        raise ValueError('This module does not certify formal regions')
    members = selection['member_dates']
    if not members or members != sorted(set(members)):
        raise ValueError('Complete explicit unique increasing members required')
    for d in members:
        day(d)
    known = day(selection['reference_known_on'])
    selected_at = timestamp(selection['actual_selected_at'])
    if selected_at is None or selected_at[:10] < known or known < members[-1]:
        raise ValueError('Distinct actual later selection and complete-source knowledge required')
    rows = [deepcopy(r) for r in payload['bars'] if r['date'] <= as_of]
    if not rows or rows[-1]['date'] != as_of or any(a['date'] >= b['date'] for a, b in zip(rows, rows[1:])):
        raise ValueError('Exact unique increasing analysis prefix required')
    if fingerprint(rows) != context['source_prefix_fingerprint']:
        raise ValueError('Analysis prefix fingerprint mismatch')
    for r in rows:
        day(r['date'])
    result = dict(schema_version=VERSION, analysis_as_of=as_of, config=deepcopy(config),
                  source_binding=deepcopy(context), evaluated_prefix_fingerprint=fingerprint(rows),
                  actual_selected_at=selection['actual_selected_at'], historical_selection_time=None,
                  selection_time_role='ACTUAL_LATER_RESEARCH_SELECTION_NOT_HISTORICAL_SIGNAL',
                  current_original_bar=deepcopy(rows[-1]), reference=None,
                  peaks=[], peak_assessments=[], pending_peaks=[], platform_ambiguities=[],
                  groups=[], highest_vote_group_ids=[], overlap_pairs=[],
                  distinct_confirmed_peak_count=0, independent_reaction_count=None,
                  candidate_anchor_diagnostic=None, reasons=[], status='UNAVAILABLE',
                  comparison_to_original_maximum=compare(None, None, 'REFERENCE_NOT_YET_KNOWN'),
                  representative_volume_line=dict(status='NOT_IMPLEMENTED', value=None),
                  formal_price_bounds=None, formal_region_membership=None,
                  execution_qualified=False, imputed_close=None, valuation=None,
                  historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False,
                  physical_android='NOT_TESTED_NEW_BUILD',
                  limitations=deepcopy(payload.get('limitations', {})))
    if as_of < known:
        result['reasons'] = ['REFERENCE_NOT_YET_KNOWN']
        return _finish(result)
    part = [r for r in rows if members[0] <= r['date'] <= members[-1]]
    actual = [r['date'] for r in part]
    bad = []
    if actual != members:
        bad.append('MISSING_OR_UNEXPECTED_EXPLICIT_MEMBER_DATES')
    if fingerprint(part) != selection['member_fingerprint']:
        bad.append('MEMBER_FINGERPRINT_CONFLICT')
    gaps = [d for d in payload.get('known_gap_dates', []) if members[0] <= day(d) <= as_of]
    breaks = [d for d in payload.get('basis_break_dates', []) if members[0] <= day(d) <= as_of]
    if any(d <= members[-1] for d in gaps):
        bad.append('KNOWN_SOURCE_MEMBER_GAP')
    if breaks:
        bad.append('BASIS_INTERRUPTION')
    for row in [r for r in rows if r['date'] >= members[0]]:
        if any(row.get(key, context[key]) != context[key] for key in SCOPE):
            bad.append('ROW_SOURCE_BASIS_VERSION_UNIT_CONFLICT')
        row_known = day(row.get('known_on', row['date']))
        if row.get('complete', True) is not True or row_known > as_of or row_known < row['date']:
            bad.append('SOURCE_RECORD_INCOMPLETE_OR_NOT_YET_KNOWN')
    for row in part:
        value = row.get('volume_shares_scaled')
        if value is None:
            bad.append('MISSING_SOURCE_VOLUME')
        else:
            try:
                v = number(value)
                if v <= 0:
                    bad.append('ZERO_SOURCE_VOLUME_UNDEFINED_PEAK_RESEARCH' if v == 0 else 'NEGATIVE_SOURCE_VOLUME')
            except ValueError:
                bad.append('INVALID_EXACT_SOURCE_VOLUME')
    try:
        validate_candles(part)
    except ValueError as error:
        bad.append('INVALID_SOURCE_OHLCV:'+str(error))
    ref = dict(candidate_id=selection['candidate_id'], qualification='RESEARCH_CANDIDATE',
               formal_price_bounds=None, formal_region_membership=None,
               member_dates=deepcopy(members), expected_records=len(members), actual_records=len(part),
               missing_dates=[d for d in members if d not in actual],
               unexpected_dates=[d for d in actual if d not in members],
               source_start=members[0], source_end=members[-1], evaluation_as_of=as_of,
               member_fingerprint=fingerprint(part), reference_known_on=known,
               actual_selected_at=selection['actual_selected_at'], source_rows=deepcopy(part),
               maximum=None, maximum_original_bars=[], completeness='UNAVAILABLE',
               calendar_qualification='EXPLICIT_SAVED_MEMBERS_NOT_COMPLETE_MARKET_CALENDAR',
               known_gap_dates=gaps, basis_break_dates=breaks)
    result['reference'] = ref
    if bad:
        result.update(status='REFUSED_SOURCE_EVIDENCE', reasons=sorted(set(bad)))
        result['comparison_to_original_maximum'] = compare(None, None, 'UNAVAILABLE_FULL_SOURCE_MAXIMUM')
        return _finish(result)
    # Reuse unchanged maximum/all-tie helper; never its total as a representative.
    values = [number(r['volume_shares_scaled']) for r in part]
    with localcontext() as ctx:
        ctx.prec = max(v.adjusted() for v in values) - min(v.as_tuple().exponent for v in values) + len(str(len(values))) + 4
        stats = volume_facts(part)
    ref.update(maximum={key: deepcopy(stats[key]) for key in ('max_single_day_shares', 'max_single_day_dates')},
               maximum_original_bars=[deepcopy(r) for r in part if r['date'] in stats['max_single_day_dates']],
               completeness='COMPLETE_EXPLICIT_SAVED_MEMBERS_ONLY')
    current = rows[-1].get('volume_shares_scaled'); current_bad = []
    try:
        if current is None or number(current) <= 0:
            current_bad.append('MISSING_OR_NONPOSITIVE_CURRENT_VOLUME')
        validate_candles([rows[-1]])
    except ValueError:
        current_bad.append('INVALID_CURRENT_OHLCV')
    if any(d > members[-1] for d in gaps):
        current_bad.append('GAP_BETWEEN_REFERENCE_AND_CURRENT')
    comparison_reason = ';'.join(current_bad) or 'AVAILABLE'
    result['comparison_to_original_maximum'] = compare(None if current_bad else current,
        stats['max_single_day_shares'], comparison_reason)
    assessments, peaks, ambiguous = _peaks(part, k, known)
    result.update(peak_assessments=assessments, peaks=peaks,
                  pending_peaks=[deepcopy(p) for p in assessments if p['status'] == 'PENDING_RIGHT_RECORDS'],
                  platform_ambiguities=ambiguous, distinct_confirmed_peak_count=len(peaks))
    if ambiguous:
        result.update(status='REFUSED_PLATFORM_AMBIGUITY', reasons=['EQUAL_VOLUME_PLATFORM_RULE_UNDEFINED_NO_FIRST_DAY_SELECTION'])
        return _finish(result)
    result['groups'] = _groups(peaks, ratio, config, ref, None if current_bad else current, comparison_reason)
    best = max((g['vote_count'] for g in result['groups']), default=0)
    result['highest_vote_group_ids'] = [g['id'] for g in result['groups'] if g['vote_count'] == best]
    for i, a in enumerate(result['groups']):
        for b in result['groups'][i+1:]:
            shared = sorted(set(a['member_dates']) & set(b['member_dates']))
            if shared:
                result['overlap_pairs'].append(dict(a=a['id'], b=b['id'], shared_dates=shared,
                                                    independent_reactions=None))
    anchor = payload.get('candidate_anchor')
    if anchor is not None:
        matched = [g for g in result['groups'] if g['member_dates'] == anchor.get('group_member_dates')]
        when = timestamp(anchor.get('actual_selected_at'))
        if len(matched) != 1 or anchor.get('date') not in matched[0]['member_dates'] or when is None or when[:10] < matched[0]['known_on']:
            result['candidate_anchor_diagnostic'] = 'REFUSED_ANCHOR_NOT_EXPLICIT_KNOWN_OR_MEMBER_OF_ONE_GROUP'
        else:
            group = matched[0]
            row = next(r for r in group['original_bars'] if r['date'] == anchor['date'])
            group['candidate_anchor'] = dict(status='PROPOSAL_NOT_APPROVED', original_bar=deepcopy(row),
                                              value=row['volume_shares_scaled'], actual_selected_at=anchor['actual_selected_at'])
    result.update(status='RESEARCH_CANDIDATES_ONLY', reasons=current_bad)
    if result['pending_peaks']:
        result['reasons'].append('RIGHT_EDGE_PENDING_NOT_FINAL_PEAK_UNIVERSE')
    return _finish(result)
