"""Manual source routing and immutable record contract tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from manual_basis.core import fingerprint, resolve, validate_request
from manual_basis.store import ChoiceJournal


def catalogue():
    entries = []
    for key, mode, day in [('raw-old', 'RAW_CANDIDATE', '2026-09-30'),
                           ('raw-new', 'RAW_CANDIDATE', '2026-09-30'),
                           ('adjusted', 'ADJUSTED_CANDIDATE', '2026-09-30')]:
        entries.append(dict(series_key=key, code='8069', price_mode=mode,
                            as_of=day, source_id='source-'+key,
                            price_basis_id='base-'+key, frame_id='frame-'+key,
                            adjustment_version='SAVED_CANDIDATE_VERSION'))
    c = dict(schema_version='manual-basis-catalogue/0.1', entries=entries)
    c['catalogue_id'] = fingerprint(c)
    return c


def request(mode='RAW_CANDIDATE', key=None, day='2026-09-30'):
    return dict(schema_version='manual-basis-request/0.1', selection_id='choice_1',
                selected_at='2026-10-22T08:00:00+08:00', code='8069',
                price_mode=mode, as_of=day, series_key=key)


class ManualBasisTest(unittest.TestCase):
    def test_unselected_and_ambiguous_require_human_choice(self):
        self.assertEqual(resolve(catalogue(), request(None))['status'], 'REQUIRES_MODE')
        r = resolve(catalogue(), request())
        self.assertEqual(r['status'], 'REQUIRES_SOURCE')
        self.assertIsNone(r['binding'])
        self.assertFalse(r['historical_signal_eligible'])

    def test_exact_binding_and_no_date_or_mode_fallback(self):
        c = catalogue()
        q = request('ADJUSTED_CANDIDATE', 'adjusted')
        frozen = copy.deepcopy(q)
        r = resolve(c, q)
        self.assertEqual(r['binding']['series_key'], 'adjusted')
        self.assertEqual(r['binding']['price_mode'], q['price_mode'])
        self.assertEqual(r['binding']['as_of'], q['as_of'])
        self.assertEqual(q, frozen)
        self.assertEqual(resolve(c, request('ADJUSTED_CANDIDATE', None, '2026-10-16'))['status'], 'UNAVAILABLE')
        self.assertEqual(resolve(c, request('RAW_CANDIDATE', 'missing'))['status'], 'UNAVAILABLE')
        self.assertEqual(resolve(c, request('RAW_CANDIDATE', 'raw-old'))['binding']['series_key'], 'raw-old')

    def test_journal_no_overwrite_and_tamper_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = ChoiceJournal(tmp)
            r = resolve(catalogue(), request('ADJUSTED_CANDIDATE', 'adjusted'))
            self.assertEqual(journal.save(r), r)
            self.assertEqual(journal.save(r), r)
            path = Path(tmp) / 'choice_1.json'
            before = path.read_bytes()
            conflicting = resolve(catalogue(), request('RAW_CANDIDATE', 'raw-old'))
            with self.assertRaises(ValueError): journal.save(conflicting)
            self.assertEqual(path.read_bytes(), before)
            path.write_bytes(before.replace(b'READY_SAVED_RESEARCH', b'UNAVAILABLE'))
            with self.assertRaises(ValueError): journal.read('choice_1')

    def test_invalid_request_is_not_reinterpreted(self):
        for bad in [dict(request(), as_of='2026-02-30'),
                    dict(request(), selected_at='2026-10-22T08:00:00'),
                    dict(request(), price_mode='BEAR_AUTO'),
                    dict(request(), selection_id='../escape')]:
            with self.assertRaises(ValueError): validate_request(bad)


if __name__ == '__main__': unittest.main()
