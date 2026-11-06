"""Offline-only source adapter and explicit research writer; never fetch or update old files."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'src'))
from source_audit import parse_twse_month
from graph_core.core import fingerprint
from reaction_facts.core import BINDING, timestamp
from .core import INPUT, CONFIG_STATUS, evaluate


def digest(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def load(raw_dir, selection_path, request):
    """Reuse stored monthly bytes/meta and the small explicit member selection."""
    selected_at = timestamp(request['actual_selected_at'])
    if selected_at is None:
        raise ValueError('Explicit actual research selection time required')
    original_bytes = Path(selection_path).read_bytes()
    original = json.loads(original_bytes)
    if original.get('schema_version') != 'explicit-research-band-volume-selection/0.1':
        raise ValueError('Existing explicit selection required')
    if request['code'] != original['binding']['code'] or original['price_mode'] != 'RAW_CANDIDATE':
        raise ValueError('This offline adapter accepts explicitly matching native Raw only')
    if request['months'] != sorted(set(request['months'])):
        raise ValueError('Explicit unique increasing raw months required')
    bars, sources = [], []
    read_at = datetime.now(timezone.utc).isoformat()
    raw_dir = Path(raw_dir)
    for month in request['months']:
        stem = request['code'] + '_' + month
        raw_path = raw_dir / (stem + '.json'); meta_path = raw_dir / (stem + '_meta.json')
        raw = raw_path.read_bytes(); meta_bytes = meta_path.read_bytes(); meta = json.loads(meta_bytes)
        if hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise ValueError('Stored raw SHA mismatch: ' + stem)
        year, mon = map(int, month.split('-'))
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={year}{mon:02}01&stockNo={request['code']}"
        if meta['url'] != url or meta.get('final_url', url) != url or meta.get('http_status') not in (None, 200):
            raise ValueError('Stored URL/HTTP/identity mismatch: ' + stem)
        rows = parse_twse_month(json.loads(raw), code=request['code'], year=year, month=mon)
        bars.extend(rows)
        sources.append(dict(month=month, raw_file=raw_path.name, raw=digest(raw),
                            meta_file=meta_path.name, meta=digest(meta_bytes), url=meta['url'],
                            http_status=meta.get('http_status'),
                            http_scope='ORIGINAL_META_VALUE_NULL_MEANS_NOT_RECORDED_NOT_ASSUMED_200',
                            original_official_capture_at=meta.get('fetched_at_utc'),
                            local_reuse_observed_at=read_at, announced_at=None,
                            row_dates=[r['date'] for r in rows]))
    # Raw monthly responses can extend beyond a chosen cutoff. Do not sort,
    # synthesize or expose those later records to the pure evaluator.
    prefix = [r for r in bars if r['date'] <= request['as_of']]
    context = dict(code=request['code'],
                   source_id=fingerprint(dict(role='EXPLICIT_OFFLINE_MONTH_SOURCE_COLLECTION',
                                              files=[dict(month=s['month'], raw=s['raw']) for s in sources])),
                   price_basis_id=original['binding']['price_basis_id'],
                   source_frame_id=fingerprint(dict(as_of=request['as_of'], bars=prefix)),
                   source_prefix_fingerprint=fingerprint(prefix), price_mode=original['price_mode'],
                   adjustment_version=original['adjustment_version'], volume_unit='SHARES_REPORTED')
    members = [r for r in prefix if r['date'] in original['member_dates']]
    selection = {key: context[key] for key in BINDING[:3] + ('price_mode', 'adjustment_version', 'volume_unit')}
    selection.update(binding={key: context[key] for key in BINDING}, candidate_id=original['candidate_id'],
                     member_dates=deepcopy(original['member_dates']), member_fingerprint=fingerprint(members),
                     reference_known_on=original['reference_known_on'], actual_selected_at=selected_at,
                     qualification='RESEARCH_CANDIDATE', formal_price_bounds=None, formal_region_membership=None)
    payload = dict(schema_version=INPUT, as_of=request['as_of'], context=context, selection=selection,
                   bars=prefix, known_gap_dates=deepcopy(request['known_gap_dates']),
                   basis_break_dates=deepcopy(request['basis_break_dates']),
                   limitations=dict(calendar='EXPLICIT_SAVED_MEMBERS_NOT_COMPLETE_MARKET_CALENDAR',
                                    known_gap_scope=request['known_gap_scope'],
                                    corporate_actions='UNVERIFIED_RAW_NOT_COMMON_ADJUSTED_PRESSURE',
                                    historical_publication='UNVERIFIED_NOT_BACKFILLED_FROM_CAPTURE',
                                    member_qualification='RESEARCH_CANDIDATE_FORMAL_MEMBERSHIP_NULL',
                                    strategy='NO_AUTOMATIC_BAND_PRIMARY_PRESSURE_OR_TRADING_RULES'))
    manifest = dict(schema_version='offline-volume-peak-source-lineage/0.1', sources=sources,
                    original_explicit_selection=digest(original_bytes),
                    original_selection_binding=deepcopy(original['binding']),
                    original_selection_time=original['selected_at'],
                    original_binding_role='SAVED_FULL_HISTORY_ARTIFACT_LINK_NOT_REVALIDATED_BY_READING_LARGE_ARTIFACT',
                    research_binding_role='NEW_SMALL_RAW_COLLECTION_AND_CUTOFF_PREFIX_NOT_ORIGINAL_FRAME_ID',
                    source_collection_id=context['source_id'],
                    native_share_parser='existing source_audit.parse_twse_month',
                    requested_as_of=request['as_of'], actual_selected_at=selected_at,
                    no_network_requests=True, no_indicator_graph_p03_or_original_band_volume_run=True)
    return payload, manifest


def write_new(path, obj):
    body = (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(body)
    return digest(body)


def build(out, raw_dir, selection_path, request):
    payload, source_manifest = load(raw_dir, selection_path, request)
    out = Path(out)
    if out.exists():
        raise ValueError('Refuse existing research output directory')
    results = []
    for probe in request['probes']:
        config = dict(k=probe['k'], r=probe['r'], qualification=CONFIG_STATUS)
        results.append((probe, evaluate(payload, config=config)))
    out.mkdir(parents=True)
    files = {}
    files['research-input.json'] = write_new(out/'research-input.json', payload)
    files['source-lineage.json'] = write_new(out/'source-lineage.json', source_manifest)
    files['research-request.json'] = write_new(out/'research-request.json', request)
    summary = []
    for index, (probe, result) in enumerate(results, 1):
        name = f'probe-{index:02}.json'
        files[name] = write_new(out/name, result)
        tied = [g for g in result['groups'] if g['id'] in result['highest_vote_group_ids']]
        summary.append(dict(file=name, config=result['config'], status=result['status'],
                            confirmed_peaks=len(result['peaks']), pending_peaks=len(result['pending_peaks']),
                            maximal_groups=len(result['groups']), highest_vote_group_count=len(tied),
                            highest_vote_groups=[dict(id=g['id'], votes=g['vote_count'],
                                min=g['min_volume_shares'], max=g['max_volume_shares'], member_dates=g['member_dates'],
                                comparisons=g['comparisons']) for g in tied]))
    files['summary.json'] = write_new(out/'summary.json', dict(
        schema_version='explicit-volume-peak-probe-summary/0.1', probes=summary,
        probe_order='SERIALIZATION_ONLY_NOT_RANKING', unique_winner_selected=False,
        independent_market_samples=None, representative_volume_line=dict(status='NOT_IMPLEMENTED', value=None)))
    write_new(out/'MANIFEST.json', dict(files=files, source_input='research-input.json',
                                      no_old_files_modified=True, product_or_source_version_changed=False))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.out, args.raw_dir, args.selection, json.loads(args.request.read_bytes()))
    print(json.dumps([dict(file=r['file'], k=r['config']['k'], r=r['config']['r'], peaks=r['confirmed_peaks'],
                           groups=r['maximal_groups'], tied_groups=r['highest_vote_group_count']) for r in result], indent=2))
