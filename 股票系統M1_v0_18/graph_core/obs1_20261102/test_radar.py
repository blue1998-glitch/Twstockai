from copy import deepcopy
from pathlib import Path
import tempfile,unittest,json
from graph_core.obs1_20261102.build_demo import fixture
from graph_core.market_daily import Journal
from graph_core.event_radar import project,STOP
from graph_core.core import analyze,fingerprint

class RadarTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        _,self.batch=fixture(self.root);self.stock=self.batch['stocks'][0]
        self.saved=Journal(self.root/'results').read(self.stock['result_key'])['value'];self.result=self.saved['result']
    def test_exact_projection_counts_sources_and_no_mutation(self):
        before=deepcopy(self.result);dates=['2026-10-30','2026-10-31','2026-11-01','2026-11-02'];idx=project(self.result,self.stock,dates=dates)
        expected=[]
        for k in ['boxes','reference_candidates']:
            for i,c in enumerate(self.result[k]):
                for n,e in enumerate(c['path']['events']):
                    if e['first_observed_at'] in dates:expected.append((k,i,n,e))
        self.assertGreater(len(expected),1);self.assertEqual(len(idx['events']),len(expected));self.assertFalse(idx['pending_are_events'])
        for row,(k,i,n,e) in zip(idx['events'],expected):
            self.assertEqual(row['type'],e['type']);self.assertEqual(row['date'],e['date']);self.assertEqual(row['first_observed_at'],e['first_observed_at']);self.assertEqual(row['original_pointer'],f'/{k}/{i}/path/events/{n}')
            c=self.result[k][i];self.assertEqual(row['candidate_id'],c.get('id',c.get('pivot_id')));self.assertEqual(row['candidate_qualification'],c['qualification'])
        self.assertEqual(before,self.result)
    def test_wrong_source_state_identity_and_future_refuse(self):
        for field,value in [('status','DATA_QUALITY_REFUSED'),('code','WRONG'),('market','WRONG'),('as_of','2026-10-30')]:
            s=dict(self.stock);s[field]=value
            with self.assertRaises(ValueError):project(self.result,s)
        with self.assertRaises(ValueError):project(self.result,self.stock,dates=['2026-11-03'])
        bad=deepcopy(self.result);c=next(c for c in bad['boxes'] if c['path']['events']);c['path']['events'][0]['first_observed_at']='2026-11-03';bad['result_id']=fingerprint({k:v for k,v in bad.items() if k!='result_id'})
        with self.assertRaises(ValueError):project(bad,self.stock)
    def test_prefix_reset_no_old_event_relabel_and_pending(self):
        p=deepcopy(self.saved['input']);p['basis_break_dates']=[p['bars'][-1]['date']];r=analyze(p,as_of=p['bars'][-1]['date']);idx=project(r,self.stock)
        self.assertTrue(idx['events']);self.assertTrue(all(e['type']==STOP for e in idx['events']))
        early=p['bars'][-2]['date'];s=dict(self.stock,as_of=early);before=analyze(p,as_of=early);x=project(before,s)
        p['bars'][-1]['close']='INVALID_FUTURE';after=analyze(p,as_of=early);self.assertEqual(x,project(after,s))
    def test_no_event_short_history_and_no_analysis_calls(self):
        from unittest.mock import patch
        with patch('graph_core.core.analyze',side_effect=AssertionError('READ must not compute')):
            for code in ['NONE','SHORT']:
                s=next(s for s in self.batch['stocks'] if s['code']==code);r=Journal(self.root/'results').read(s['result_key'])['value']['result'];self.assertEqual(project(r,s)['events'],[])
if __name__=='__main__':unittest.main()
