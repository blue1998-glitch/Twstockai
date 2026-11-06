import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from .action_sources import HERE,build_catalog
from .action_study import verified_quotes,audit_windows,candidate_input,gross_schedule_preview
from .action_fixtures import fixture,event
from .action_ledger import replay
from .store import Journal


class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old,cls.manifest=verified_quotes();cls.catalog=build_catalog()
        cls.audit=audit_windows(cls.old,cls.catalog,cls.manifest)

    def test_all_prior_windows_audited_no_false_return(self):
        a=self.audit;self.assertEqual(a['planned_windows'],72);self.assertEqual(a['source_price_windows'],70)
        self.assertEqual(a['total_net_return_qualified_windows'],0)
        self.assertEqual(sum(w['end'] is None for w in a['windows']),2)
        for w in a['windows']:
            self.assertTrue(w['refusal_reasons']);self.assertEqual(len(w['plans']),6)
            self.assertTrue(all(p['total_net_return'] is None for p in w['plans'].values()))

    def test_real_archive_reader_matches_122_unchanged_inputs(self):
        self.assertEqual(len(self.manifest),122)
        self.assertEqual([(c,len(v['bars'])) for c,v in self.old['assets'].items()],[('1101',317),('2884',317)])
        nulls=[(c,b['date']) for c,v in self.old['assets'].items() for b in v['bars'] if b.get('missing')]
        self.assertEqual(nulls,[('1101','2025-08-13'),('2884','2025-11-05')])

    def test_real_cash_crossing_refused_with_specific_sources_missing(self):
        d=candidate_input(self.old,self.catalog,self.manifest,'2026-06-30','2026-07-29','1101');r=replay(d)
        self.assertEqual(r['daily'],[]);self.assertIsNone(r['total_net_return'])
        self.assertIn('NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN',r['refusal_reasons'])
        self.assertIn('ACTION_COVERAGE_INCOMPLETE:2884',r['refusal_reasons'])
        self.assertEqual(sum('net_per_share' in x for x in r['refusal_reasons']),2)

    def test_opening_on_ex_day_is_not_assumed_free_of_existing_claims(self):
        cases=[w for w in self.audit['windows'] if w['start']=='2026-07-01']
        self.assertEqual(len(cases),8)
        self.assertTrue(all(len(w['ex_events_on_opening_close'])==2 for w in cases))
        self.assertTrue(all('OPENING_ENTITLEMENTS_UNKNOWN' in w['refusal_reasons'] for w in cases))

    def test_gross_schedule_never_promotes_to_net_or_share_ratio(self):
        p=gross_schedule_preview(self.old,self.catalog);self.assertEqual(len(p['previews']),4)
        x=next(x for x in p['previews'] if x['code']=='1101' and x['ex_date']=='2026-07-01')
        self.assertEqual(x['gross_entitlement'],'16000.0')
        by_date={r['date']:r for r in x['daily']}
        self.assertEqual(by_date['2026-07-01']['gross_dividend_receivable'],'16000.0')
        self.assertEqual(by_date['2026-07-27']['issuer_scheduled_cumulative_gross_paid'],'0')
        self.assertEqual(by_date['2026-07-28']['issuer_scheduled_cumulative_gross_paid'],'16000.0')
        self.assertIsNone(by_date['2026-07-28']['available_net_cash'])
        self.assertFalse(x['actual_payment_confirmed'])

    def test_cli_run_read_byte_equal_and_conflicting_id_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input.json';d=fixture();event(d);p.write_text(json.dumps(d))
            base=[sys.executable,'-m','rotation_research.action_cli']
            args=['--store',td+'/records','--id','cash-example']
            run=subprocess.run(base+['RUN','--input',str(p)]+args,cwd=HERE.parent,capture_output=True,check=True)
            read=subprocess.run(base+['READ']+args,cwd=HERE.parent,capture_output=True,check=True)
            self.assertEqual(run.stdout,read.stdout)
            before=(Path(td)/'records/cash-example.json').read_bytes()
            d['opening']['cash']='10';p.write_text(json.dumps(d))
            failed=subprocess.run(base+['RUN','--input',str(p)]+args,cwd=HERE.parent,capture_output=True)
            self.assertNotEqual(failed.returncode,0);self.assertIn(b'Identity conflict',failed.stderr)
            self.assertEqual((Path(td)/'records/cash-example.json').read_bytes(),before)

    def test_cli_read_never_imports_numeric_producer(self):
        from . import action_cli
        with tempfile.TemporaryDirectory() as td:
            Journal(td).save('probe',{'not_a_calculation':True})
            with patch.dict(sys.modules,{'rotation_research.action_ledger':None}),patch.object(sys,'argv',['action_cli','READ','--store',td,'--id','probe']),contextlib.redirect_stdout(io.StringIO()) as out:
                action_cli.main()
            self.assertTrue(json.loads(out.getvalue())['value']['not_a_calculation'])


if __name__=='__main__':unittest.main()
