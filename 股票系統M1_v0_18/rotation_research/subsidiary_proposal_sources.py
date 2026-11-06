"""Offline producer: bind captured PDFs and explicit manual review, never OCR or network."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
from urllib.parse import quote

from . import capital_components_sources as parent_source
from . import source_followup as quote_core
from .action_sources import ROOT, HERE, dump
from .action_scope import identify
from .subsidiary_proposal import SCHEMA, PARENT_ID, MINUTES, VOTING, PROVENANCE_SHA, facts, observation, validate, qualify, evidence_sha

OUT = HERE / 'subsidiary_proposal_20261023'
FILE_PINS = {'pdf-extraction-verification.json': 'cd6a2fd72e8e08a3d58f3393464baf6a5c429a8ed37ddcc858eb147dec86fe4e', 'raw/tcc-egm-minutes-20261013.meta.json': '4d6c17a70910ff82e08f087052d6e27cc086bb5cdc825e92e5c6d8dd10d8fd46', 'raw/tcc-egm-minutes-20261013.response': '861283c21d87e0511c43485874592102dc8d4a73099271a5d23edcbf5dc44b7b', 'raw/tcc-egm-minutes-20261013.txt': '009391559b2777d7003b4a8f2ac076416b66eee634361c208c85dae6d174cda0', 'raw/tcc-egm-voting-20261013.meta.json': 'db0298c89ab942a3c41621e181a81ef893c5356f0a18bd7fdd9d6e3d5a8c9270', 'raw/tcc-egm-voting-20261013.response': 'af2524a2a9ef722266fd82dceb95fbc5c4a0222793a0f965bbc27266aec48154', 'raw/tcc-egm-voting-20261013.txt': '0085499789e79cf719053d3c744f08f509bc7bfb3bbcac7c2d28b377927c0801', 'source-manifest.json': 'daf0eb2432524af66ed31cf4ca44e1c5d558217a2b29a7b9bb8f2a7ea07765c6', 'visual/tcc-egm-minutes-20261013-p1.png': '9b6b0c52845fd2f2b6b3a49c2678101f6cb03696a14a92e8c1e8c9522b79bb59', 'visual/tcc-egm-minutes-20261013-p2.png': '23d6d729b20577238b2afd643f11eb9fb9bf423fe3ad80eaeeb8df8e5755e3f1', 'visual/tcc-egm-minutes-20261013-p3.png': '2635ba2bbf7e0766da5e9e36e2da8a30999db7029bdcf24cbd0e51f5994b0a50', 'visual/tcc-egm-minutes-20261013-p4.png': 'b39303e2c869ce2d1f6e60fc2215b8d4b45fe70c260923f69c2ac99652dc9686', 'visual/tcc-egm-voting-20261013-p1.png': 'e0cd43d7afadf19f7f0bf1f60ebeb84bba68d514549884ea3e8ba526dd0e9d3e', 'visual-review.json': '45f149c988922aee224f264a1bce3516fd3f5058e208e896248bdff2c428c0df'}


def sha(body): return hashlib.sha256(body).hexdigest()


def load_source(folder=OUT, root=ROOT):
    folder, root = Path(folder), Path(root)
    for name, digest in FILE_PINS.items():
        if sha((folder / name).read_bytes()) != digest: raise ValueError('Captured original/meta/derivative changed: ' + name)
    m = json.loads((folder / 'source-manifest.json').read_text())
    if evidence_sha(m) != PROVENANCE_SHA: raise ValueError('Source manifest changed')
    index = (root / m['index']['path']).read_bytes()
    if sha(index) != m['index']['sha256'] or len(index) != m['index']['bytes']: raise ValueError('Archived index mismatch')
    html = index.decode(); section = html.split('2026第一次股東臨時會</h2>', 1)[1].split('</section>', 1)[0]
    if '2026.10.13' not in section: raise ValueError('Wrong index meeting section')
    native = {}
    for sid in [MINUTES, VOTING]:
        meta = json.loads((folder / 'raw' / (sid + '.meta.json')).read_text())
        body = (folder / 'raw' / (sid + '.response')).read_bytes()
        if (m['official_captures'][sid] != meta or meta['http'] != 200 or meta['status'] != 'CAPTURED'
                or meta['bytes'] != len(body) or meta['sha256'] != sha(body) or not body.startswith(b'%PDF-')
                or meta['url'] != quote(meta['original_href'], safe=':/%') or meta['final_url'] != meta['url']
                or meta['redirects_followed'] is not False or meta['retries'] != 0
                or ('href="' + meta['original_href'] + '"') not in section):
            raise ValueError('Original source/URL/HTTP/index binding mismatch')
        native[sid] = (folder / 'raw' / (sid + '.txt')).read_text()
    review = json.loads((folder / 'visual-review.json').read_text())
    if review != m['visual_review']: raise ValueError('Manual review cannot be replaced by synthetic native text')
    for entry in review['images']:
        p = root / entry['path']; body = p.read_bytes()
        if sha(body) != entry['sha256'] or len(body) != entry['bytes']: raise ValueError('Reviewed page image changed')
    return dict(manifest=m, native_evidence=native)


def build_catalog(folder=OUT):
    source = load_source(folder); base = parent_source.build_catalog()
    if base['id'] != PARENT_ID or base != json.loads((parent_source.OUT / 'catalog-v09.json').read_text()):
        raise ValueError('Exact complete frozen parent0.9 required')
    f = facts(source)
    return validate(identify(dict(schema=SCHEMA, parent_catalog_id=base['id'], parent_catalog=deepcopy(base),
        coverage=deepcopy(base['coverage']), source=source, facts=f, observations=[observation(source, f)],
        historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)))


def study_input(old, catalog, manifest, calendar, start, end, code):
    result = parent_source.study_input(old, catalog['parent_catalog'], manifest, calendar, start, end, code)
    result['subsidiary_proposal_catalog_id'] = catalog['id']
    return result


def run():
    catalog = build_catalog(); old, manifest = parent_source.verified_quotes(); calendar = parent_source.build_calendar()
    qcatalog = catalog
    while qcatalog['schema'] != quote_core.SCHEMA: qcatalog = qcatalog['parent_catalog']
    missing = [quote_core.quote_diagnostic(qcatalog, c, b['date'], b['close'], b['date'] in calendar['sessions'])
        for c, a in old['assets'].items() for b in a['bars'] if b.get('missing')]
    if dict(diagnostics=missing) != json.loads((parent_source.OUT / 'missing-quotes.json').read_text()):
        raise AssertionError('Missing-quote history must remain byte-semantic exact')
    design = json.loads((HERE / 'generated/design.json').read_text()); dates = [b['date'] for b in old['assets']['1101']['bars']]; windows = []
    for start in design['cutoffs']:
        for a, b in [('1101', '2884'), ('2884', '1101')]:
            for horizon in design['horizons']:
                i = dates.index(start)
                if i + horizon >= len(dates):
                    windows.append(dict(A=a, B=b, start=start, end=None, horizon=horizon, status='INSUFFICIENT_SAVED_FORWARD_ROWS'))
                else:
                    q = qualify(study_input(old, catalog, manifest, calendar, start, dates[i+horizon], a), catalog)
                    if q['daily'] or q['journal'] or q['total_net_return'] is not None or q['original_numeric_replay_called']:
                        raise AssertionError('Subsidiary plan source cannot authorize net accounting')
                    windows.append(dict(A=a, B=b, horizon=horizon, **q))
    summary = dict(schema=SCHEMA, new_official_originals=2, official_network_requests=2, old_esun_pdf_requests=0,
        scanned_minutes_pages_reviewed=[1, 2, 3, 4], native_voting_pages_reviewed=[1],
        detailed_scan_clause_parser='NOT_IMPLEMENTED_INVENTORY_ONLY', exact_parent_v09_id=catalog['parent_catalog_id'],
        observations=len(catalog['observations']), numeric_ledger_events_added=0, independent_market_samples_added=0,
        canonical_meeting_ordinal=None, announced_at=None, actual_effective_at=None,
        original_quote_archives_rechecked=len(manifest), calendar_reports_rechecked=len(calendar['sources']),
        qualification_calls=sum(w['end'] is not None for w in windows),
        refused_windows=sum(w['status'] == 'REFUSED_INCOMPLETE_EVENT_ACCOUNTING' for w in windows),
        insufficient_windows=sum(w['end'] is None for w in windows),
        exchange_unsupported_windows=sum('SHARE_EXCHANGE_ACCOUNT_IMPACT_UNSUPPORTED' in w.get('refusal_reasons', []) for w in windows),
        qualified_total_net_return_windows=sum(w.get('total_net_return') is not None for w in windows),
        numeric_replay_calls=sum(bool(w.get('original_numeric_replay_called')) for w in windows), six_strategy_replays=0,
        missing_quotes_exact_parent_preserved=True, parent_nulls_preserved=True, work_github_readback_at=None,
        android='NOT_TESTED_NEW_BUILD', historical_signal_eligible=False, primary_pressure_id=None, policy_authorized=False)
    return {'catalog-v010.json': catalog, 'missing-quotes.json': dict(diagnostics=missing),
        'window-qualification.json': dict(windows=windows, ranking=None), 'verification.json': summary}


def main():
    values = run()
    for name, value in values.items():
        p = OUT / name
        if p.exists() and json.loads(p.read_text()) != value: raise ValueError('Frozen source output differs; choose new version: ' + name)
        if not p.exists(): dump(p, value)
    print(json.dumps(values['verification.json']))


if __name__ == '__main__': main()
